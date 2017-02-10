# Under MIT license, see LICENSE.txt
from .Action import Action
# from ...Util.types import AICommand
from RULEngine.Util.constant import PLAYER_PER_TEAM
from ai.Util.ai_command import AICommand, AICommandType



class Idle(Action):
    """
    Action Stop: Arrête le robot
    Méthodes :
        exec(self): Retourne la position du joueur qui l'a appelé
    Attributs (en plus de ceux de Action):
        player_id : L'identifiant du joueur
    """
    def __init__(self, p_game_state, p_player_id):
        """
            :param p_game_state: L'état courant du jeu.
            :param p_player_id: Identifiant du joueur qui s'arrête
        """
        Action.__init__(self, p_game_state)
        assert(isinstance(p_player_id, int))
        assert PLAYER_PER_TEAM >= p_player_id >= 0
        self.player_id = p_player_id

    def exec(self):
        """
        Exécute l'arrêt
        :return: Un tuple (None, kick) où None pour activer une commande de stop et kick est nul (on ne botte pas)
        """
        # un None pour que le coachcommandsender envoi une command vide.
        move_destination = None
        kick_strength = 0
        return AICommand(self.player_id, AICommandType.STOP)
