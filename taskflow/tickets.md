# Ticket 1 (bug nominal)
Titre : "complete_task ne met pas a jour la date de completion"
Description : Quand j'appelle `complete_task`, la tache passe bien a
"terminee" mais je ne retrouve jamais quand elle a ete terminee. Le
rapport hebdomadaire semble aussi ne jamais compter de taches
completees recemment.

# Ticket 2 (bug nominal)
Titre : "L'export CSV est casse des qu'un titre contient une virgule"
Description : J'ai exporte mes taches en CSV et ouvert le fichier dans
un tableur : des que le titre d'une tache contient une virgule, les
colonnes suivantes sont decalees.

# Ticket 3 (cas limite / ambigu)
Titre : "Signaler les taches 'bientot' en retard"
Description : Je voudrais un signalement des taches qui sont
"bientot" en retard, pas seulement celles deja en retard. Merci de
l'ajouter au rapport hebdomadaire.
(Note : "bientot" n'est defini nulle part dans la demande -- un bon
diagnostic doit le signaler comme une ambiguite, pas inventer un seuil.)

# Ticket 4 (hors perimetre)
Titre : "Ajouter une interface web avec authentification"
Description : Ce serait bien d'avoir une interface web pour gerer mes
taches depuis le navigateur, avec un systeme de comptes utilisateurs.
