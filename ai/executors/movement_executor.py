
from RULEngine.Util.constant import POSITION_DEADZONE
from RULEngine.Util.Pose import Pose
from ai.executors.executor import Executor
from ai.Debug.debug_interface import DebugInterface


class MovementExecutor(Executor):

    def __init__(self, p_world_state):
        super().__init__(p_world_state)
        self.debug_interface = DebugInterface()
        self.path_shared = 0
    def exec(self):
        self._simple_advance_path()

    def _simple_advance_path(self):
        current_ai_c = self.ws.play_state.current_ai_commands

        for ai_c in current_ai_c.values():
            if len(ai_c.path) > 0:
                self.path_shared=ai_c.path
                next_point = ai_c.path[0]
                # TODO ORIENTATION! PLEASES!
                ai_c.pose_goal = Pose(next_point, 0)
