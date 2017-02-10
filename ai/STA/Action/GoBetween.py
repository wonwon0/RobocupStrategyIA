# Under MIT licence, see LICENCE.txt
import math
from ..Action.Action import Action
# from ...Util.types import AICommand
from RULEngine.Util.Pose import Pose
from RULEngine.Util.Position import Position
from RULEngine.Util.area import stayOutsideCircle
from RULEngine.Util.geometry import get_angle, get_distance
from RULEngine.Util.constant import PLAYER_PER_TEAM
from ai.Util.ai_command import AICommand, AICommandType


__author__ = 'Robocup ULaval'


class GoBetween(Action):
    """
    Action GoBetween: Déplace le robot au point le plus proche sur la droite entre deux positions passées en paramètres
    Méthodes :
        exec(self): Retourne la pose où se rendre
    Attributs (en plus de ceux de Action):
        player_id : L'identifiant du joueur
        position1 : La première position formant la droite
        position2 : La deuxième position formant la droite
        target : La position vers laquelle le robot devrait s'orienter
        minimum_distance : La distance minimale qu'il doit y avoir entre le robot et chacun des points
    """
    def __init__(self, p_game_state, p_player_id, p_position1, p_position2, p_target, p_minimum_distance=0):
        """
            :param p_game_state: L'état courant du jeu.
            :param p_player_id: Identifiant du joueur qui doit se déplacer
            :param p_position1: La première position formant la droite
            :param p_position2: La deuxième position formant la droite
            :param p_target: La position vers laquelle le robot devrait s'orienter
            :param p_minimum_distance: La distance minimale qu'il doit y avoir entre le robot et chacun des points
        """
        Action.__init__(self, p_game_state)
        assert(isinstance(p_player_id, int))
        assert PLAYER_PER_TEAM >= p_player_id >= 0
        assert(isinstance(p_position1, Position))
        assert(isinstance(p_position2, Position))
        assert(isinstance(p_target, Position))
        assert(isinstance(p_minimum_distance, (int, float)))
        # TODO check this assert one day MGL 2017/01/13
        # assert(get_distance(p_position1, p_position2) > 2*p_minimum_distance)

        self.player_id = p_player_id
        self.position1 = p_position1
        self.position2 = p_position2
        self.target = p_target
        self.minimum_distance = p_minimum_distance

    def exec(self):
        """
        Calcul le point le plus proche du robot sur la droite entre les deux positions
        :return: Un tuple (Pose, kick) où Pose est la destination du joueur et kick est nul (on ne botte pas)
        """
        robot_position = self.game_state.get_player_pose(self.player_id).position
        delta_x = self.position2.x - self.position1.x
        delta_y = self.position2.y - self.position1.y

        if delta_x != 0 and delta_y != 0:   # droite quelconque
            # Équation de la droite reliant les deux positions
            a1 = delta_y / delta_x                                  # pente
            b1 = self.position1.y - a1*self.position1.x             # ordonnée à l'origine

            # Équation de la droite perpendiculaire
            a2 = -1/a1                                              # pente perpendiculaire à a1
            b2 = robot_position.y - a2*robot_position.x             # ordonnée à l'origine

            # Calcul des coordonnées de la destination
            x = (b2 - b1)/(a1 - a2)                                 # a1*x + b1 = a2*x + b2
            y = a1*x + b1
        elif delta_x == 0:  # droite verticale
            x = self.position1.x
            y = robot_position.y
        elif delta_y == 0: # droite horizontale
            x = robot_position.x
            y = self.position1.y

        destination_position = Position(x, y)

        # Vérification que destination_position se trouve entre position1 et position2
        distance_positions = math.sqrt(delta_x**2 + delta_y**2)
        distance_dest_pos1 = get_distance(self.position1, destination_position)
        distance_dest_pos2 = get_distance(self.position2, destination_position)

        if distance_dest_pos1 >= distance_positions and distance_dest_pos1 > distance_dest_pos2:
            # Si position2 est entre position1 et destination_position
            new_x = self.position2.x - self.minimum_distance * delta_x / distance_positions
            new_y = self.position2.y - self.minimum_distance * delta_y / distance_positions
            destination_position = Position(new_x, new_y)
        elif distance_dest_pos2 >= distance_positions and distance_dest_pos2 > distance_dest_pos1:
            # Si position1 est entre position2 et destination_position
            new_x = self.position1.x + self.minimum_distance * delta_x / distance_positions
            new_y = self.position1.y + self.minimum_distance * delta_y / distance_positions
            destination_position = Position(new_x, new_y)

        # Vérification que destination_position respecte la distance minimale
        if distance_dest_pos1 <= distance_dest_pos2:
            destination_position = stayOutsideCircle(destination_position, self.position1, self.minimum_distance)
        else:
            destination_position = stayOutsideCircle(destination_position, self.position2, self.minimum_distance)

        # Calcul de l'orientation de la pose de destination
        destination_orientation = get_angle(destination_position, self.target)

        destination_pose = {"pose_goal": Pose(destination_position, destination_orientation)}
        kick_strength = 0

        return AICommand(self.player_id, AICommandType.MOVE, **destination_pose)
