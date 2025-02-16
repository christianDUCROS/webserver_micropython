################################
##### MODULE SERVEUR WEB ####### 
#NE  PAS MODIFIER CE MODULE 
################################
import gc
gc.collect()

import network
import socket
import time
#parametre du serveur
import parametres  
repertoire = parametres.repertoire
index_page = parametres.index_page
ssid = parametres.ssid
password = parametres.password

#module de gestion interne et capteurs 
import mgic 
#module  traitement de commandes dynamiques   
import mtcd

#led allumée durant les échanges client-serveur
from machine import Pin
Led_builtin = Pin('LED', Pin.OUT)
Led_builtin.off()

def connexion_wifi_STA(pssid,ppassword) : # Connexion wifi mode STATION

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(pssid, ppassword)

    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('Serveur connecté à la borne wifi : ', pssid)
        status = wlan.ifconfig()
        print( 'Adresse serveur web : ' + status[0] )
        Led_builtin.on()
        time.sleep(3)
        Led_builtin.off()

def connexion_wifi_AP(pssid,ppassword): #Connexion wifi mode ACCESS POINT
    wlan = network.WLAN(network.AP_IF)
    wlan.config(essid= pssid , password = ppassword)
    wlan.active(True)
    wlan.config(pm = 0xa11140) #augmente la réactivité
    while wlan.active == False :
        pass
    print("Access point actif")
    print('Réseau wifi : ',pssid, 'et mot de passe :',ppassword)
    print('Adresse serveur web : ',wlan.ifconfig()[0],'\t masque de réseau : ',wlan.ifconfig()[1])
    Led_builtin.on()
    time.sleep(3)
    Led_builtin.off()

def insertion_valeurs_dynamiques (fichier_lu) :
    debut_recherche = 0
    while True :
        # recherche du premier {{
        start = fichier_lu.find(b"{{", debut_recherche)
        if start ==-1 :
            break
        end = fichier_lu.find(b"}}", start)
        nom_variable = fichier_lu[start + 2:end].strip()
        nom_variable_str = nom_variable.decode()
        valeur_nom_variable = dico_valeurs_dynamiques.get(nom_variable_str)
        if valeur_nom_variable != None :
            fichier_lu = fichier_lu[0:start]+ valeur_nom_variable + fichier_lu[end+2::]   
        #recherche de la prochaine insertion capteur 
        debut_recherche = end + 2
    return fichier_lu


def acquisition_commande(request_file_name) :
    print(request_file_name)
    #analyse de la requête, recherche de la commande        
    commande = ''
    if "/?" in request_file_name:
        indice_debut = request_file_name.find("?")+1
        commande = request_file_name[indice_debut:]
        Led_builtin.off()
        #gc.collect()
    return commande
 
def get_request_file(request_file_name):
    #page index par défaut
    if request_file_name == '/' :  
        request_file_name = '/'+index_page
    with open(repertoire + request_file_name, 'rb') as file:   #byte
        file_requested= file.read()
        print(repertoire + request_file_name)
    file_requested = insertion_valeurs_dynamiques(file_requested)  
    return file_requested

################################################################
#debut programme principal

#connexion wifi
if parametres.mode_wifi== 'AP' : 
    connexion_wifi_AP(ssid,password)
elif parametres.mode_wifi== 'STA' :
    connexion_wifi_STA(ssid,password)

#Construction dico_valeurs_dynamiques
dico_valeurs_dynamiques = {} 

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
time.sleep(5)
s = socket.socket()
s.bind(addr)
s.listen(5)
s.settimeout(2)
print('Ecoute des connexions sur : ', addr) # Listen for connections
 
while True:
    commande=''
    #Mise à jour donnéees dynamiques : Capteurs....
    dico_valeurs_dynamiques = mgic.gestion_interne_et_affichages_capteurs(dico_valeurs_dynamiques)
    try:
        cl, addr = s.accept()
        #Allume LED pour indiquer un client connecté 
        Led_builtin.on()
        #reception de la demande
        request = cl.recv(1024)
        #turns the request into a string
        request = str(request)        
        #recherche des donnémtcd.traitement_commandes_dynamiques(commande)es demandées
        request = request.split()[1]
        if '.html' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n'
        elif '.css' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: text/css\r\n\r\n'
        elif '.js' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: text/javascript\r\n\r\n'
        elif '.svg' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: image/svg+xml\r\n\r\n'
        elif '.json' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: application/json\r\n\r\n'  #json
        elif '.svgz' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: image/svg+xml\r\n\r\n'
        elif '.png' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: image/png\r\n\r\n'
        elif '.ico' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: image/x-icon\r\n\r\n'
        elif '.jpg' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: image/jpg\r\n\r\n'
        elif '.webp' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: image/webp\r\n\r\n'   #webp
        # serve index if you don't know
        else:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n'
        #lecture du ficher demandé + recherche commande  
        #recherche d'une commande
        print(request)
        commande = acquisition_commande(request)
        print('la commande est :',commande)
        #mtcd.traitement_commandes_dynamiques(commande) #traitement commandes dynamiques
        #pas de commande = simple appel de page
        if commande=='' :
            #lecture du ficher demandé + insertion data 
            response = get_request_file(request)
            #envoie file header
            cl.send(file_header)
            #envoie réponse
            cl.sendall(response)
            cl.close()
            #eteindre la led  : fin de la communication
            Led_builtin.off()
        cl.close()
    except :
        try:
            cl.close()
        except :
            pass
        Led_builtin.off()
        print('pas de connexion http')
    mtcd.traitement_commandes_dynamiques(commande)

'''
if __name__=='__main__' :
    activer_serveur_web()
'''
