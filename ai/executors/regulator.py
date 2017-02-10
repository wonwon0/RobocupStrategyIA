# Under MIT License, see LICENSE.txt
import math

import time

from RULEngine.Util.Pose import Pose
from RULEngine.Util.Position import Position
from RULEngine.Util.game_world import GameWorld
from ai.Util.ai_command import AICommandType
from ai.executors.executor import Executor
from ai.states.game_state import GameState
import numpy as np

INTEGRAL_DECAY = 0.5 # reduit de moitié aux 1/8 de secondes
ZERO_ACCUMULATOR_TRHESHOLD = 0.5
FILTER_LENGTH = 1
REGULATOR_DEADZONE = 120

SIMULATION_MAX_NAIVE_CMD = math.sqrt(2) / 3
SIMULATION_MIN_NAIVE_CMD = 0
SIMULATION_MAX_THETA_CMD = math.pi / 8
SIMULATION_MIN_THETA_CMD = 0
SIMULATION_DEFAULT_STATIC_GAIN = 0.0009
SIMULATION_DEFAULT_INTEGRAL_GAIN = 0
SIMULATION_DEFAULT_THETA_GAIN = 1

REAL_MAX_NAIVE_CMD = 1200
REAL_DEADZONE_CMD = 110
REAL_MIN_NAIVE_CMD = REAL_DEADZONE_CMD
REAL_MAX_THETA_CMD = 300
REAL_MIN_THETA_CMD = 30
REAL_DEFAULT_STATIC_GAIN = 0.300
REAL_DEFAULT_INTEGRAL_GAIN = 0.600
REAL_DEFAULT_THETA_GAIN = 350
REAL_DEFAUT_INTEGRAL_THETA_GAIN = 0
#REAL_DEFAULT_THETA_GAIN = 0


class PositionRegulator(Executor):
    def __init__(self, p_world_state: GameWorld, is_simulation=False):
        super().__init__(p_world_state)
        self.regulators = [PI(simulation_setting=is_simulation) for _ in range(6)]
        self.last_timestamp = 0

    def exec(self):
        commands = self.ws.play_state.current_ai_commands
        delta_t = self.ws.game_state.game.delta_t
        for cmd in commands.values():
            if cmd.command is AICommandType.MOVE:
                robot_idx = cmd.robot_id
                retroaction_pose = self.ws.game_state.get_player_pose(robot_idx)
                cmd.pose_goal = self.regulators[robot_idx].\
                    update_pid_and_return_speed_command(cmd.pose_goal, retroaction_pose, delta_t, idx=robot_idx)


class PI(object):
    """
        Asservissement PI en position

        u = Kp * err + Sum(err) * Ki * dt
    """

    def __init__(self, simulation_setting=True):
        self.gs = GameState()
        self.accumulator_x = 0
        self.accumulator_y = 0
        self.accumulator_t = 0
        self.constants = _set_constants(simulation_setting)
        self.kp = self.constants['default-kp']
        self.ki = self.constants['default-ki']
        self.ktheta = self.constants['default-ktheta']
        self.itheta = self.constants['default-itheta']
        self.last_command_x = 0
        self.last_command_y = 0
        self.previous_cmd = []
        self.last_err_x = 0
        self.last_err_y = 0

    def update_pid_and_return_speed_command(self, pose_goal, player_pose, delta_t=0.030, idx=4, robot_speed=0.75):
        """ Met à jour les composants du pid et retourne une commande en vitesse. """
        assert isinstance(pose_goal, Pose), "La consigne doit etre une Pose dans le PI"
        print(pose_goal)

        #if self.gs.paths is not None:
        #    print('YOLOYOLOYOLOYOLOYOLOYOLOYOLOYOLOYOLO', self.gs.paths[idx])
        if self.gs.paths.get(idx) and pose_goal is not self.gs.paths[idx][-1]:
        #if False:
            cmd = pose_goal
            r_x, r_y = pose_goal.position.x, pose_goal.position.y
            t_x, t_y = player_pose.position.x, player_pose.position.y
            e_x = (r_x - t_x)/100
            e_y = (r_y - t_y)/100
            vit = np.array([e_x, e_y])
            if np.linalg.norm(vit) > 1:
                vit /= np.linalg.norm(vit)
            elif np.linalg.norm(vit) < 0.25:
                cmd.position = Position(0, 0)
                return cmd
            vit *= robot_speed
            cmd.position = Position(vit[0], vit[1])
            return cmd
        else:
            r_x, r_y = pose_goal.position.x, pose_goal.position.y
            t_x, t_y = player_pose.position.x, player_pose.position.y
            e_x = r_x - t_x
            e_y = r_y - t_y

            # composante proportionnel
            up_x = self.kp * e_x
            up_y = self.kp * e_y

            # composante integrale, decay l'accumulator
            ui_x, ui_y = self._compute_integral(delta_t, e_x, e_y)
            if idx == 4:
                #print("({}) accumulateur: {}, {}".format(delta_t, self.accumulator_x, self.accumulator_y))
                pass
            self._zero_accumulator()

            u_x = up_x + ui_x
            u_y = up_y + ui_y

            # try relinearize
            if 0 < abs(u_x) < self.constants['deadzone-cmd']:
                if u_x > 0:
                    u_x = self.constants['deadzone-cmd']
                else:
                    u_x = -self.constants['deadzone-cmd']
            elif abs(u_x) < self.constants['deadzone-cmd']:
                u_x = 0

            if 0 < abs(u_y) < self.constants['deadzone-cmd']:
                if u_y > 0:
                    u_y = self.constants['deadzone-cmd']
                else:
                    u_y = -self.constants['deadzone-cmd']
            elif abs(u_y) < self.constants['deadzone-cmd']:
                u_y = 0

            # correction frame reference et saturation
            x, y = self._referential_correction_saturation(player_pose, u_x, u_y)

            # correction de theta
            # FIXME: extract PI logic
            e_theta = pose_goal.orientation - player_pose.orientation
            theta = self.ktheta * e_theta
            self.accumulator_t += self.itheta * e_theta
            theta += self.accumulator_t
            if abs(self.accumulator_t) > REAL_MAX_THETA_CMD:
                self.accumulator_t = 0
            theta = self._saturate_orientation(theta)

            #if math.sqrt(e_x**2 + e_y**2) < REGULATOR_DEADZONE:
            #    x, y = 0, 0
            cmd = Pose(Position(x, y), theta)
            cmd = self._filter_cmd(cmd)
            cmd.orientation = theta
            distance = math.sqrt(e_x**2 + e_y**2)
            print(distance)
            if distance < REGULATOR_DEADZONE:
                x, y = 0, 0
            cmd.position = Position(x, y)
            return cmd

    def _saturate_orientation(self, theta):
        if abs(theta) > self.constants['max-theta-cmd']:
            if theta > 0:
                return self.constants['max-theta-cmd']
            else:
                return -self.constants['max-theta-cmd']
        elif abs(theta) < self.constants['min-theta-cmd']:
            return 0
        else:
            return theta

    def _referential_correction_saturation(self, player_pose, u_x, u_y):
        x, y = _correct_for_referential_frame(u_x, u_y, player_pose.orientation)

        if abs(x) > self.constants['max-naive-cmd']:
            if x > 0:
                x = self.constants['max-naive-cmd']
            else:
                x = -self.constants['max-naive-cmd']

        if abs(x) < self.constants['min-naive-cmd']:
            x = 0

        if abs(y) > self.constants['max-naive-cmd']:
            if y > 0:
                y = self.constants['max-naive-cmd']
            else:
                y = -self.constants['max-naive-cmd']

        if abs(y) < self.constants['min-naive-cmd']:
            y = 0

        return x, y

    def _compute_integral(self, delta_t, e_x, e_y):
        ui_x = self.ki * e_x * delta_t
        ui_y = self.ki * e_y * delta_t
        self.accumulator_x = (self.accumulator_x * INTEGRAL_DECAY) + ui_x
        self.accumulator_y = (self.accumulator_y * INTEGRAL_DECAY) + ui_y
        return ui_x, ui_y

    def _zero_accumulator(self):
        if self.accumulator_x < ZERO_ACCUMULATOR_TRHESHOLD:
            self.accumulator_x = 0

        if self.accumulator_y < ZERO_ACCUMULATOR_TRHESHOLD:
            self.accumulator_y = 0

    def _filter_cmd(self, cmd):
        self.previous_cmd.append(cmd)
        xsum = 0
        ysum = 0
        for cmd in self.previous_cmd:
            xsum += cmd.position.x
            ysum += cmd.position.y

        xsum /= len(self.previous_cmd)
        ysum /= len(self.previous_cmd)
        if len(self.previous_cmd) > FILTER_LENGTH:
            self.previous_cmd.pop(0)
        return Pose(Position(xsum, ysum))



def _set_constants(simulation_setting):
    if simulation_setting:
        return {'max-naive-cmd':SIMULATION_MAX_NAIVE_CMD,
                'deadzone-cmd':0,
                'min-naive-cmd':SIMULATION_MIN_NAIVE_CMD,
                'max-theta-cmd':SIMULATION_MAX_THETA_CMD,
                'min-theta-cmd':SIMULATION_MIN_THETA_CMD,
                'default-kp':SIMULATION_DEFAULT_STATIC_GAIN,
                'default-ki':SIMULATION_DEFAULT_INTEGRAL_GAIN,
                'default-ktheta':SIMULATION_DEFAULT_THETA_GAIN,
                'default-itheta':0
                }
    else:
        return {'max-naive-cmd':REAL_MAX_NAIVE_CMD,
                'deadzone-cmd':REAL_DEADZONE_CMD,
                'min-naive-cmd':REAL_MIN_NAIVE_CMD,
                'max-theta-cmd':REAL_MAX_THETA_CMD,
                'min-theta-cmd':REAL_MIN_THETA_CMD,
                'default-kp':REAL_DEFAULT_STATIC_GAIN,
                'default-ki':REAL_DEFAULT_INTEGRAL_GAIN,
                'default-ktheta':REAL_DEFAULT_THETA_GAIN,
                'default-itheta':REAL_DEFAUT_INTEGRAL_THETA_GAIN
                }


def _correct_for_referential_frame(x, y, orientation):
    cos = math.cos(-orientation)
    sin = math.sin(-orientation)

    corrected_x = (x * cos - y * sin)
    corrected_y = (y * cos + x * sin)
    return corrected_x, corrected_y
