from mpld3 import plugins
import mpld3
import matplotlib.pyplot as plt
import pandas_datareader as web
import datetime as dt
import pandas as pd
import numpy as np

class MousePositionDatePlugin(plugins.PluginBase):
    """Plugin d'affichage des coordonnées de la souris sur l'axes x en format datetime et y en euros"""

    JAVASCRIPT ="""
        mpld3.register_plugin("mousepositiondate", MousePositionDatePlugin);
        MousePositionDatePlugin.prototype = Object.create(mpld3.Plugin.prototype);
        MousePositionDatePlugin.prototype.constructor = MousePositionDatePlugin;
        MousePositionDatePlugin.prototype.requiredProps = [];
        MousePositionDatePlugin.prototype.defaultProps = {
        fontsize: 12,
        xfmt: "%Y-%m-%d",
        yfmt: ".3g"
        };
        function MousePositionDatePlugin(fig, props) {
        mpld3.Plugin.call(this, fig, props);
        }
        
        MousePositionDatePlugin.prototype.draw = function() {
        var fig = this.fig;
        var xfmt = d3.timeFormat(this.props.xfmt);
        var yfmt = d3.format(this.props.yfmt);
        var coords = fig.canvas.append("text").attr("class", "mpld3-coordinates").style("text-anchor", "end").style("font-size", this.props.fontsize).attr("x", this.fig.width - 5).attr("y", this.fig.height - 5);
        
        
        for (var i = 0; i < this.fig.axes.length; i++) {
          var update_coords = function() {
            var ax = fig.axes[i];
            return function() {
              var pos = d3.mouse(this);
              x = ax.xdom.invert(pos[0]);
              y = ax.ydom.invert(pos[1]);
              coords.text("Date: " + xfmt(x) + ", Prix : " + yfmt(y) + "");
            };
          }();
          fig.axes[i].baseaxes.on("mousemove", update_coords).on("mouseout", function() {
            coords.text("");
          });
        }
        };
        """
    def __init__(self, fontsize=14, xfmt="%Y-%m-%d", yfmt=".3g"):
        self.dict_ = {"type": "mousepositiondate",
                      "fontsize": fontsize,
                      "xfmt": xfmt,
                      "yfmt": yfmt}

def get_data(crypto="BTC-EUR",start=dt.datetime(2020, 8, 1),end=dt.datetime.now()):
    #Les valeurs de la crypto sont entre 2020 et maintenant par defaut
    start = dt.datetime(2020, 8, 1)
    end = dt.datetime.now()
    data = web.DataReader(crypto, "yahoo", start, end)
    return crypto,data,start,end


def get_crypto_prediction(nb_days=10):
    """
    Génere les prédictions des nb_days prochains jours
    :return: dataframe dates_prediction et prediction
    """
    #============Generation of predictions=====
    prediction_days = nb_days # = n

    #Create scaled dataframe
    df = pd.DataFrame(data["Close"])
    df.reset_index(inplace=True)
    df.columns = ["Dates","Prices"]
    df.pop("Dates")

    df['Predictions'] = df[["Prices"]].shift(-prediction_days) #Crée la collone de prédiction

    scaled_data_x = np.array(df.drop(["Predictions"],1))[:len(df)-prediction_days]#Convert the df to a list and remove the last 'n' rows
                                                                     #where 'n' is 0 prediction_days
    #Convertis le dataframe en liste et enleve les 'n' dernières lignes ou 'n' est la variable prediction_days
    scaled_data_y = np.array(df["Predictions"])[:-prediction_days]

    #Sépare la data en 80% pour l'entrainement et 20% pour le test
    from sklearn.model_selection import  train_test_split
    x_train,x_test,y_train,y_test = train_test_split(scaled_data_x,scaled_data_y, test_size=0.2)

    #Definis la variable 'prediction_days_array' comme les 'prediction_days' dernières lignes de df
    prediction_days_array = np.array(df.drop(["Predictions"],1))[-prediction_days:]

    #Crée et entraine la Support Vector Machine (Regression) en utilisant une fonction en base radial
    from sklearn.svm import SVR
    svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.00001)
    svr_rbf.fit(x_train,y_train)

    #Entraine le modèle
    svr_rbf_confidence = svr_rbf.score(x_test, y_test)

    #Prend les prédictions
    svm_prediction = svr_rbf.predict(x_test)

    #Affiche les prédictions
    svm_prediction = svr_rbf.predict(prediction_days_array)

    #Convertis les valeurs en un nouveau dataframe
    dates_prediction = pd.date_range(end,periods=prediction_days,freq='1d')
    prediction = pd.DataFrame({'Dates': dates_prediction,'Prices':svm_prediction})
    #=====Fin de la partie prédiction==============================
    return dates_prediction,prediction

def create_courbe():
    """
    Crée les courbes et renvoie l'html corresponsdants
    :return:
    """
    crypto_colors = {"BTC-EUR":"#0b78e9","ETH-EUR":"#37367b","DOGE-EUR":"#e1b303"}
    df = data
    close_prices = df["Close"]
    # plot line + confidence interval
    fig, ax = plt.subplots()
    ax.grid(True, alpha=0.2)

    l = ax.plot(close_prices.index, close_prices.values,str(crypto_colors[nom_crypto]),label="Courbe")
    ax.fill_between(close_prices.index,
                    list(df["Low"]), list(df["High"]),
                    color=crypto_colors[nom_crypto], alpha=0.5)

    #Trace les courbes de prédiction
    prediction.loc[0,"Dates"] = close_prices.index[-1]
    prediction.loc[0,"Prices"] = close_prices[-1]

    ax.plot(prediction["Dates"],prediction["Prices"],linestyle="--")


    #Crée la légende interactive

    handles, labels = ax.get_legend_handles_labels() # return lines and labels
    interactive_legend = plugins.InteractiveLegendPlugin(zip(handles,
                                                             ax.collections),
                                                         labels,
                                                         alpha_unsel=0.5,
                                                         alpha_over=1.5,
                                                         start_visible=True)

    plugins.connect(fig, interactive_legend)
    plugins.connect(fig, MousePositionDatePlugin())

    #Définition des courbes, des légendes et des couleurs
    ax.set_ylim(min(data["Close"]),max(data["Close"]))
    ax.set_ylabel('Euros')
    ax.set_xlabel(nom_crypto)
    ax.set_title(str('Courbe '+nom_crypto), size=20)
    ax.set_facecolor("#222222")

    #Sauvegarde l'html de la courbe
    mpld3.save_html(plt.gcf(),str('courbes_'+nom_crypto+'.html'))

def get_value_and_variation(data):
    """
    Renvoie les valeurs et les variations des cryptomonnaie
    :param data: les valeurs des crypto
    :return: tuple avec la derniere valeur de la crypto et son taux de variation avec le jour précédent
    """
    variation = str(round(((data["Close"][-2]-data["Close"][-1])/data["Close"][-2])*100,3))
    if float(variation)> 0:
        variation = "+" + variation
    return str(round(data["Close"][-1],2)),variation

def create_html_courbes(cryptos_values_var):
  html = """
                <ul>
                    <li>
                        <h5>BITCOIN BTC-EUR_VALUE </h5>
                        <p> BTC-EUR_VARIATION </p>
                    </li>
                    <li>
                        <h5>ETHERUM ETH-EUR_VALUE </h5>
                        <p> ETH-EUR_VARIATION </p>
                    </li>
                    <li>
                        <h5>DOGECOIN DOGE-EUR_VALUE </h5>
                        <p> DOGE-EUR_VARIATION </p>
                    </li>
                </ul>
            </section>
            <section id = "courbes">
                <h1>SUIVRE LES COURBES</h1>
  """
  liste_html = html.split()
  for index in cryptos_values_var.keys():
    liste_html[liste_html.index(index)] = cryptos_values_var[index]
  html = "\n".join(liste_html)

  with open("chiffres.txt", "w", encoding="utf-8") as html_file:
    html_file.write(html)

#=======Main Program====
cryptos_values_test = {"BTC-EUR_VALUE":str(0), "BTC-EUR_VARIATION": str(0),
                      "ETH-EUR_VALUE":str(0), "ETH-EUR_VARIATION": str(0),
                      "DOGE-EUR_VALUE":str(0), "DOGE-EUR_VARIATION": str(0)}

cryptos_values_var = dict()
list_crypto = ["BTC-EUR","ETH-EUR","DOGE-EUR"]
for crypto in list_crypto:
    nom_crypto,data,start,end = get_data(crypto)
    cryptos_values_var[nom_crypto+"_VALUE"],cryptos_values_var[nom_crypto+"_VARIATION"] = get_value_and_variation(data)
    print(cryptos_values_var)
    dates_prediction,prediction = get_crypto_prediction(10)
    create_courbe()

create_html_courbes(cryptos_values_var)