"""
    Module définissant les **Exception** du moteur de l'intelligence
    artificielle et des stratégies.
"""

class StopPlayerError(Exception):
    """
        Est levée si le moteur est incapable d'envoyer la commande pour arrêter
        les joueurs.
    """
    pass
