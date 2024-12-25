import socket
import threading

class ClientJeu:
    def __init__(self, host='localhost', port=2410): # Le client doit se connecter sur le même port que le serveur 
        self.host = host
        self.port = port
        self.client_socket = None

    def connecter(self):
        """Connexion au serveur."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket Internet avec le protocole TCP
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Connexion refusée par le serveur. Le jeu a peut-être déjà commencé.")
            return False
        return True

    def recevoir_messages(self):
        """Thread pour recevoir des messages du serveur."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"\n{message}")  # Afficher le message reçu
            except socket.error:
                print("Connexion au serveur perdue.")
                break

    def envoyer_message(self, message):
        """Envoyer un message au serveur."""
        try:
            self.client_socket.send(message.encode()) # Coder le message en bits pour l envoyer 
        except socket.error as e:
            print(f"Erreur lors de l'envoi du message: {e}")

    def jouer(self):
        """Boucle principale du jeu."""
        if not self.connecter():
            return

        # Démarrer un thread pour recevoir les messages en arrière-plan
        thread_reception = threading.Thread(target=self.recevoir_messages)
        thread_reception.start()

        print("Vous êtes connecté ! Tapez un message pour discuter ou 'quit' pour quitter.")

        while True:
            # Lire l'entrée utilisateur
            choix = input()

            # Quitter le jeu
            if choix.lower() == 'quit':
                self.envoyer_message("quit")
                print("Vous avez quitté le jeu.")
                break

            # Envoyer le message (peut être un choix ou un message de chat)
            self.envoyer_message(choix)

        self.client_socket.close()


if __name__ == "__main__": # Point d'entrée pour l'exécution du code
    client = ClientJeu()
    client.jouer()
