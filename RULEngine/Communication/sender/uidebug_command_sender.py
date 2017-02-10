# Under MIT License, see LICENSE.txt

import pickle

from RULEngine.Communication.util.udp_socket import udp_socket


class UIDebugCommandSender(object):
    """
        Définition du service capable d'envoyer des paquets de débogages au
        serveur et à l'interface de débogage. S'occupe de la sérialisation.
    """
    def __init__(self, host, port):
        """ Constructeur """
        self.server = udp_socket(host, port)

    def _send_packet(self, p_packet):
        """ Envoi un seul paquet. """
        try:
            self.server.send(pickle.dumps(p_packet))
        except ConnectionRefusedError:
            # FIXME: hack
            pass

    def send_command(self, p_packets):
        """ Reçoit une liste de paquets et les envoies. """
        for packet in p_packets:
            self._send_packet(packet)