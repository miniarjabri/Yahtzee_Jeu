import socket
import threading
import random

class Server:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.parties = {}
        self.next_game_id = 1
        self.lock = threading.Lock()

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Le serveur est démarré et attend des connexions...")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connexion acceptée de {client_address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        print("Gestion d'un nouveau client...")
        partie = self.choisir_partie(client_socket)
        if partie is None:
            print("Aucune partie sélectionnée. Fermeture de la connexion.")
            client_socket.close()
            return

        client_socket.send("Bienvenue au jeu de Yahtzee ! Veuillez entrer votre nom : ".encode())
        nom_client = client_socket.recv(1024).decode().strip()

        with self.lock:
            joueur_id = len(partie.joueurs) + 1
            partie.ajouter_joueur(nom_client, client_socket, joueur_id)
            print(f"{nom_client} (ID: {joueur_id}) a rejoint la partie {partie.id_partie}")

            if not partie.jeu_commence:
                partie.commencer_partie()
                print(f"Partie {partie.id_partie} commence avec {len(partie.joueurs)} joueur(s).")

        partie.gerer_client(client_socket, nom_client)

    def choisir_partie(self, client_socket):
        while True:
            print("Envoi de la liste des parties disponibles...")
            if self.parties:
                client_socket.send("Parties disponibles :\n".encode())
                for id_partie, partie in self.parties.items():
                    status = "commencée" if partie.jeu_commence else "non commencée"
                    client_socket.send(f"Partie {id_partie} ({status}) \n".encode())
            else:
                client_socket.send("Aucune partie disponible. Vous pouvez créer une nouvelle partie.\n".encode())

            client_socket.send("Tapez l'ID de la partie pour la rejoindre ou 'nouvelle' pour en créer une : ".encode())
            choix = client_socket.recv(1024).decode().strip()

            if choix.lower() == "nouvelle":
                with self.lock:
                    id_partie = self.next_game_id
                    partie = Partie(id_partie)
                    self.parties[id_partie] = partie
                    self.next_game_id += 1
                print(f"Nouvelle partie créée avec l'ID {id_partie}")
                client_socket.send(f"Nouvelle partie {id_partie} créée.\n".encode())
                return partie

            try:
                id_partie = int(choix)
                if id_partie in self.parties:
                    partie = self.parties[id_partie]
                    if partie.jeu_commence:
                        print(f"La partie {id_partie} est déjà commencée.")
                        client_socket.send("La partie a déjà commencé. Veuillez choisir une autre partie ou créer une nouvelle.\n".encode())
                    else:
                        print(f"Le client rejoint la partie {id_partie}")
                        client_socket.send(f"Vous avez rejoint la partie {id_partie}.\n".encode())
                        return partie
                else:
                    print(f"ID de partie invalide : {id_partie}")
                    client_socket.send("Partie invalide. Veuillez réessayer.\n".encode())
            except ValueError:
                print("Entrée non valide pour la sélection de la partie.")
                client_socket.send("Entrée non valide. Veuillez réessayer.\n".encode())





if __name__ == "__main__":
    server = Server()
    server.start()
