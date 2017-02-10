# Under MIT license, see LICENSE.txt
from .Action import Action
from RULEngine.Util.Pose import Pose
from RULEngine.Util.constant import PLAYER_PER_TEAM
from ai.Util.ai_command import AICommand, AICommandType


class AllStar(Action):
    """
    Action Stop: Arrête le robot
    Méthodes :
        exec(self): Retourne la position du joueur qui l'a appelé
    Attributs (en plus de ceux de Action):
        player_id : L'identifiant du joueur
    """
    def __init__(self, p_game_state, p_player_id, **other_args):
        """
            :param p_game_state: L'état courant du jeu.
            :param p_player_id: Identifiant du joueur qui s'arrête
        """
        Action.__init__(self, p_game_state)
        assert(isinstance(p_player_id, int))
        assert PLAYER_PER_TEAM >= p_player_id >= 0
        self.player_id = p_player_id
        self.other_args = {"dribbler_on": other_args.get("dribbler_on", False),
                           "pathfinder_on": other_args.get("pathfinder_on", False),
                           "kick_strength": other_args.get("kick_strength", 0),
                           "charge_kick": other_args.get("charge_kick", False),
                           "pose_goal": other_args.get("pose_goal", Pose())
                           }
        self.ai_command_type = other_args.get("ai_command_type", AICommandType.MOVE)

        # this is for the pathfinder only no direct assignation
        # TODO put that correctly
        self.path = other_args.get("path", [])

    def exec(self):
        """
        Exécute l'arrêt
        :return: Un tuple (None, kick) où None pour activer une commande de stop et kick est nul (on ne botte pas)
        """
        # un None pour que le coachcommandsender envoi une command vide.

        return AICommand(self.player_id, self.ai_command_type, **self.other_args)
