import create_courbes #Cette ligne permet d'executer le programme afin de créer les courbes
filenames = ['start_html.txt', 'chiffres.txt', 'courbes_BTC-EUR.html','courbes_ETH-EUR.html','courbes_DOGE-EUR.html', 'end_html.txt']
#Le code ci-dessous permet de concatener les fichiers texte de filenames
with open('../index.html', 'w') as outfile:
    for fname in filenames:
        with open(fname) as infile:
            for line in infile:
                outfile.write(line)

