
import os
import requests
from flask import Flask, request, render_template_string

API_KEY = "be6bffb6c37bffb2be9f1ecbdc4b77f8"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

app = Flask(__name__)

def search_team(team_name):
    url = f"{BASE_URL}/teams"
    params = {"search": team_name}
    response = requests.get(url, headers=HEADERS, params=params).json()
    data = response["response"]
    if data:
        return data[0]["team"]["id"], data[0]["team"]["name"]
    return None, None

def get_last_matches(team_id, nb=3):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": nb}
    response = requests.get(url, headers=HEADERS, params=params).json()
    return [m for m in response["response"] if m["fixture"]["status"]["short"] == "FT"]

def get_team_ranking(team_id):
    # Essaye de récupérer le classement à partir du dernier match joué en championnat
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": 5}
    matches = requests.get(url, headers=HEADERS, params=params).json()["response"]
    for match in matches:
        league = match["league"]
        if league["type"] == "League":
            season = league["season"]
            league_id = league["id"]
            return fetch_ranking(league_id, season, team_id)
    return None

def fetch_ranking(league_id, season, team_id):
    url = f"{BASE_URL}/standings"
    params = {"league": league_id, "season": season}
    res = requests.get(url, headers=HEADERS, params=params).json()
    standings = res["response"]
    if standings:
        for team in standings[0]["league"]["standings"][0]:
            if team["team"]["id"] == team_id:
                return f"{team['rank']}ᵉ dans {standings[0]['league']['name']}"
    return None

def build_html(team_name, team_id, matches, ranking):
    if not matches:
        return f"<p>Aucun match trouvé pour <strong>{team_name}</strong></p>"

    total = 0
    rows = ""
    for m in matches:
        date = m["fixture"]["date"][:10]
        comp = m["league"]["name"]
        is_home = m["teams"]["home"]["id"] == team_id
        opponent = m["teams"]["away"]["name"] if is_home else m["teams"]["home"]["name"]
        gf = m["goals"]["home"] if is_home else m["goals"]["away"]
        ga = m["goals"]["away"] if is_home else m["goals"]["home"]
        total += gf
        result = "Victoire" if gf > ga else "Défaite" if gf < ga else "Nul"
        rows += f"<tr><td>{date}</td><td>{opponent}</td><td>{comp}</td><td>{gf}-{ga}</td><td>{result}</td></tr>"

    classement_html = f"<p><strong>Classement :</strong> {ranking}</p>" if ranking else ""

    return f'''
<h2>Résultats récents de {team_name}</h2>
<table border="1" cellpadding="6">
    <tr><th>Date</th><th>Adversaire</th><th>Compétition</th><th>Score</th><th>Résultat</th></tr>
    {rows}
</table>
<p><strong>Total de buts marqués :</strong> {total}</p>
{classement_html}
'''

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    if request.method == "POST":
        team = request.form.get("team")
        print("Recherche pour :", team)

        team_id, team_name = search_team(team)
        print("Résultat search_team :", team_id, team_name)

        if team_id:
            matches = get_last_matches(team_id)
            print("Matchs récupérés :", len(matches))
            ranking = get_team_ranking(team_id)
            print("Classement :", ranking)
            result = build_html(team_name, team_id, matches, ranking)
        else:
            result = f"<p style='color:red;'>❌ Équipe non trouvée.</p>"

    return render_template_string("""
<html>
<head>
    <title>Derniers matchs - API Football</title>
</head>
<body>
    <h1>Rechercher une équipe de football</h1>
    <form method="post">
        <input type="text" name="team" placeholder="ex: Marseille, Red Star..." required>
        <input type="submit" value="Rechercher">
    </form>
    <hr>
    {{result|safe}}
</body>
</html>
""", result=result)

if __name__ == "__main__":
    app.run(debug=True)
