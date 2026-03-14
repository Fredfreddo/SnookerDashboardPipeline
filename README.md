# 🔴 Snooker Elo Analytics & Dashboard

An automated data pipeline and interactive dashboard designed to track, analyze, and predict professional snooker performance. This project utilizes custom Elo-based algorithms to to track player's "live" form by considering extra information such as abilities to make 70+ breaks and form decay/recovery.

## 🚀 Live Demo
**Check out the live dashboard here:** [https://snooker-elo-score.streamlit.app/]

**Check out my article explaining the math of two methods:** [https://fredfreddo.github.io/2026/03/13/Snooker-ELO-Inspired-Scores-and-Dashboard/]

---

## 🛠 Project Architecture
This repository features a fully automated ETL (Extract, Transform, Load) pipeline that coordinates Java-based data processing with a Python-based (streamlit) frontend.

### 1. Data Acquisition (Java + Selenium)
The pipeline begins with `UpdateCrawler.java`. Every day, it has one single visit to [cuetracker.net](https://cuetracker.net/)'s current season page and its latest tournament page to check if there's new WST match data and updates the existing series of JSON files (since 2022-2023 season).

### 2. Analytical Engine (Java + Maven)
Once the raw match data is stored in season-specific JSON files, two distinct algorithms process the history:
* **Modified Elo (Method A):** Incorporates standard match results update plus a factor for 70+ breaks..
* **Live Form Index (Method B):** Uses expected frames won, the 70+ breaks factor, plus temporal decay & recovery.
* Two csv files are generated with all players' scores based on these 2 methods and their time-series history.

### 3. Interactive Dashboard (Python + Streamlit)
The results are visualized in web app.
- **Rankings:** View historical rankings on any specific date based on selected method.
- **Trajectories:** Compare the scores history of multiple players over time based on selected method.
- **Match Predictor:** An interactive tool to simulate win probabilities and most likely scorelines based on selected methodologies and match lengths.

---

## My article on this project
- [Explaining the math of two methods](https://fredfreddo.github.io/2026/03/13/Snooker-ELO-Inspired-Scores-and-Dashboard/)

---

## Data Sources
- [cuetracker.net](https://cuetracker.net/)
- [snooker.org](https://snooker.org/)
