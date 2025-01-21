import socket
import threading

class ClientJeu:
    def __init__(self, host='localhost', port=2410):
        self.host = host
        self.port = port
        self.client_socket = None

    def connecter(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Connexion refusée par le serveur.")
            return False
        return True

    def recevoir_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"\n{message}")
            except socket.error:
                print("Connexion perdue avec le serveur.")
                break

    def envoyer_message(self, message):
        try:
            self.client_socket.send(message.encode())
        except socket.error as e:
            print(f"Erreur d'envoi : {e}")

    def jouer(self):
        if not self.connecter():
            return

        thread_reception = threading.Thread(target=self.recevoir_messages)
        thread_reception.start()

        while True:
            message = input()
            if message.lower() == "quit":
                self.envoyer_message("fin")
                print("Vous avez quitté la partie.")
                break
            self.envoyer_message(message)

        self.client_socket.close()


if __name__ == "__main__":
    client = ClientJeu()
    client.jouer()
