import socket

class Client:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print("Connexion au serveur réussie.")
        except ConnectionRefusedError:
            print("Connexion refusée par le serveur.")
            return False
        return True

    def play_game(self):
        if not self.connect():
            return

        try:
            while True:
                message = self.client_socket.recv(1024).decode()

                if not message:  # Server closed connection
                    print("Connexion fermée par le serveur.")
                    break

                print(f"Message du serveur : {message}")

                # Handle specific messages from the server
                if "nom" in message:
                    choix = input("Entrez votre nom : ")
                    self.client_socket.send(choix.encode())

                elif "ID de la partie" in message:
                    choix = input("Entrez votre choix : ")
                    self.client_socket.send(choix.encode())

                elif "valeur des dés à garder" in message:
                    choix = input("Entrez la valeur des dés à garder (ex: 5) ou tapez 'fin' : ")
                    self.client_socket.send(choix.encode())

                elif "relancer" in message or "terminer" in message:
                    choix = input("Entrez 'oui' ou 'non' : ")
                    self.client_socket.send(choix.encode())

        finally:
            self.client_socket.close()
            print("Déconnexion du serveur.")

if __name__ == "__main__":
    client = Client()
    client.play_game()
