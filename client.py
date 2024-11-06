import socket

class ClientJeu:
    def __init__(self, host='localhost', port=2410):
        self.host = host
        self.port = port
        self.client_socket = None

    def connecter(self):
        """Connexion au serveur."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Connexion refusée par le serveur. Le jeu a peut-être déjà commencé.")
            return False
        return True

    def recevoir_message(self):
        """Recevoir un message du serveur."""
        try:
            message = self.client_socket.recv(1024).decode()
            return message
        except socket.error as e:
            print(f"Erreur lors de la réception du message: {e}") 
            return None

    def envoyer_message(self, message):
        """Envoyer un message au serveur."""
        try:
            self.client_socket.send(message.encode())
        except socket.error as e:
            print(f"Erreur lors de l'envoi du message: {e}")

    def jouer(self):
        """Boucle principale du jeu."""
        if not self.connecter():
            return

        while True:
            message = self.recevoir_message()
            if not message:
                break
            print(message)

            # Si le serveur demande le nom du joueur
            if "nom" in message:
                choix = input("Entrez votre nom : ")
                self.envoyer_message(choix)

            # Si la partie est terminée pour ce joueur, attendre les autres joueurs
            elif "terminé vos tours" in message:
                print("En attente des autres joueurs...")

            # Si c'est l'annonce du gagnant, on ferme la connexion
            elif "Le gagnant est" in message:
                print("Annonce du gagnant reçue, fermeture de la connexion.")
                break

            # Si le serveur indique que le jeu a déjà commencé
            elif "Le jeu a déjà commencé" in message:
                print("Connexion refusée. Le jeu a déjà commencé avec un certain nombre de joueurs.")
                break

            # Si le serveur attend une réponse
            elif "valeur" in message :
                choix = input("Entrez votre choix : ")
                self.envoyer_message(choix)

        self.client_socket.close()


if __name__ == "__main__":
    client = ClientJeu()
    client.jouer()
