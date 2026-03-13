import com.google.gson.Gson;
import org.apache.commons.math3.util.CombinatoricsUtils;

import java.io.*;
import java.util.*;

public class JsonProcessor {
    private Map<String, Player> players = new HashMap<>();
    private static final double K_BASE = 32.0;
    private static final double FRAME_WON_PARAMETER = 400.0;
    private static final double BREAK_MULTIPLIER = 25.0;
    private static final double INITIAL_POINTS_GAP = 10.0;
    private static final String INITIAL_DATE = "2022-06-27";

    public Map<String, Player> getPlayers() {
        return players;
    }


    // read json file (such as "season_2023-2024.json")
    // make a sorted list of matches by date, from oldest to newest,
    // return the list of matches
    public List<Match> readMatchesFromJson(String fileName) {
            Gson gson = new Gson();
            try (Reader reader = new FileReader(fileName)) {
                Season season = gson.fromJson(reader, Season.class);
                List<Match> matches = new ArrayList<>();
                int index = 0;
                for (Tournament tournament : season.getTournaments()) {
                    for  (Match match : tournament.getMatches()) {
                        match.setOriginalIndex(index);
                        matches.add(match);
                        index++;
                    }
                }
                // sort matches by date, from oldest to newest
                // if same date, maintain the reverse of original order
                // (so that the matches in the same tournament are in the same order as in the json file)
                matches.sort(Comparator.comparing(Match::getDate)
                        .thenComparing(Comparator.comparingInt(Match::getOriginalIndex).reversed()));
                return matches;
            } catch (IOException e) {
                e.printStackTrace();
                return Collections.emptyList();
            }
    }

    // calculate expected frames won for each player based
    public List<Double> calculateExpectedFramesWonForTwoPlayers(int bestOfFrames, double player1Points, double player2Points) {
        // 1. Calculate Single-Frame Win Probability
        // This predicts the chance of Player 1 winning any given frame
        double expectedFrameProbP1 = 1.0 / (1.0 + Math.pow(Math.E, (player2Points - player1Points) / FRAME_WON_PARAMETER));
        double expectedFrameProbP2 = 1.0 - expectedFrameProbP1;

        double expectedFramesP1 = 0.0;
        double expectedFramesP2 = 0.0;

        int reachToWin = bestOfFrames / 2 + 1;
        // if player1 won
        for  (int i = 0; i <= (bestOfFrames - reachToWin); i++) {
            double resultProb = Math.pow(expectedFrameProbP1, reachToWin) * Math.pow(expectedFrameProbP2, i) *
                    CombinatoricsUtils.binomialCoefficient(reachToWin + i - 1, i);
            expectedFramesP1 += resultProb * reachToWin;
            expectedFramesP2 += resultProb * i;
        }
        // if player2 won
        for  (int i = 0; i <= (bestOfFrames - reachToWin); i++) {
            double resultProb = Math.pow(expectedFrameProbP2, reachToWin) * Math.pow(expectedFrameProbP1, i) *
                    CombinatoricsUtils.binomialCoefficient(reachToWin + i - 1, i);
            expectedFramesP1 += resultProb * i;
            expectedFramesP2 += resultProb * reachToWin;
        }
        // if bestOfFrames is 4, add 2-2 case
        if (bestOfFrames % 2 == 0) {
            double resultProb = Math.pow(expectedFrameProbP1, bestOfFrames / 2) * Math.pow(expectedFrameProbP2, bestOfFrames / 2) *
                    CombinatoricsUtils.binomialCoefficient(bestOfFrames, bestOfFrames / 2);
            expectedFramesP1 += resultProb * bestOfFrames / 2;
            expectedFramesP2 += resultProb * bestOfFrames / 2;
        }

        return Arrays.asList(expectedFramesP1, expectedFramesP2);
    }

    public double calculateGlobalBreakRate(List<Match> matches) {
        int totalPlayerFrames = 0;
        int total70PlusBreaks = 0;

        for (Match match : matches) {
            int framesPlayed = match.getPlayer1Score() + match.getPlayer2Score();

            totalPlayerFrames += framesPlayed;

            total70PlusBreaks += match.getBreaksPlayer1().stream().filter(b -> b >= 70).count();
            total70PlusBreaks += match.getBreaksPlayer2().stream().filter(b -> b >= 70).count();
        }

        double globalRate = totalPlayerFrames == 0 ? 0 : (double) total70PlusBreaks / totalPlayerFrames;
        System.out.printf("Global 70+ Break Rate: %.4f per player-frame\n", globalRate);
        return globalRate;
    }

    // process the sorted list of matches
    // for each match, if a player does not exist in the players set,
    // initialize a new player with the player's name and country using constructor,
    // and add the player to the players set
    public void processMatches(List<Match> matches) {
        double globalBreakRate = calculateGlobalBreakRate(matches);
        for (Match match : matches) {
            String player1Name = match.getPlayer1();
            String player2Name = match.getPlayer2();
            String player1Country = match.getPlayer1Country();
            String player2Country = match.getPlayer2Country();
            String date = match.getDate();
            // if date is like "2023-04-01", fine
            // if date is like "2024-05-05 - 05-06", take latest date "2024-05-06"
            // essentially, combine first 5 characters and last 5 characters to get the latest date
            date = date.substring(0, 5) + date.substring(date.length() - 5);

            if (!players.containsKey(player1Name)) {
                Player player1 = new Player(player1Name, player1Country);
                player1.addScoreDate(date, player1.getCurrentFormPoints());
                players.put(player1Name, player1);
            }
            if (!players.containsKey(player2Name)) {
                Player player2 = new Player(player2Name, player2Country);
                player2.addScoreDate(date, player2.getCurrentFormPoints());
                players.put(player2Name, player2);
            }

            // now get players' points
            Player player1 = players.get(player1Name);
            Player player2 = players.get(player2Name);
            double player1Points = player1.getCurrentFormPoints();
            double player2Points = player2.getCurrentFormPoints();
            int player1Score = match.getPlayer1Score();
            int player2Score = match.getPlayer2Score();
            int bestOfFrames = match.getBestOfFrames();
            // get how many 70+ breaks each player has
            int player1Breaks70Plus = (int)match.getBreaksPlayer1().stream().filter(breakScore -> breakScore >= 70)
                    .count();
            int player2Breaks70Plus = (int)match.getBreaksPlayer2().stream().filter(breakScore -> breakScore >= 70)
                    .count();

            // calculate expected score for player 1
            // 1. Calculate Single-Frame Win Probability
            // This predicts the chance of Player 1 winning any given frame
            double expectedFrameProbP1 = 1.0 / (1.0 + Math.pow(Math.E, (player2Points - player1Points) / FRAME_WON_PARAMETER));
            double expectedFrameProbP2 = 1.0 - expectedFrameProbP1;

            // 2. Calculate Expected Frames Won
            int totalFramesPlayed = player1Score + player2Score;
            double expectedFramesP1 = expectedFrameProbP1 * totalFramesPlayed;
            double expectedFramesP2 = expectedFrameProbP2 * totalFramesPlayed;

            // 3. Base Points Change (Zero-Sum)
            // Note: We don't need the Math.sqrt(bestOfFrames) scaling anymore.
            // A longer match naturally has a higher totalFramesPlayed, which inherently scales the points change!
            double pointsChangePlayer1 = K_BASE * (player1Score - expectedFramesP1);
            double pointsChangePlayer2 = K_BASE * (player2Score - expectedFramesP2);

            double expectedBreaksP1 = globalBreakRate * player1Score;
            double expectedBreaksP2 = globalBreakRate * player2Score;

            pointsChangePlayer1 += BREAK_MULTIPLIER * (player1Breaks70Plus - expectedBreaksP1);
            pointsChangePlayer2 += BREAK_MULTIPLIER * (player2Breaks70Plus - expectedBreaksP2);
            // add bonus for 70+ breaks, set as 400 * count / bestOfFrames
//            pointsChangePlayer1 += 400.0 * player1Breaks70Plus / bestOfFrames;
//            pointsChangePlayer2 += 400.0 * player2Breaks70Plus / bestOfFrames;
            // update players' points
            player1.setCurrentFormPoints(player1Points + pointsChangePlayer1);
            player2.setCurrentFormPoints(player2Points + pointsChangePlayer2);

            // add score date for both players
            player1.addScoreDate(date, player1.getCurrentFormPoints());
            player2.addScoreDate(date, player2.getCurrentFormPoints());
        }
    }

    public void initializePlayers(String fileName){
        // read rankings_22_23.csv and initialize players with the points in the csv file
        try (BufferedReader br = new BufferedReader(new FileReader(fileName))) {
            String line;
            // skip the header
            br.readLine();
            while ((line = br.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length >= 3) {
                    String name = parts[2].trim();
                    String country = parts[1].trim();
                    int ranking = Integer.parseInt(parts[0].trim().replaceAll("[^\\d-]", ""));

                    double points = 1500.0 + (65.5 - ranking) * INITIAL_POINTS_GAP;
                    Player player = new Player(name, country, points);
                    player.addScoreDate(INITIAL_DATE, points);
                    players.put(name, player);
                }
            }
        }
        catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void deleteBannedPlayers(){
        // remove banned players
        players.remove("Yan Bingtao");
        players.remove("Liang Wenbo");
        players.remove("Li Hang");
        players.remove("Lu Ning");
        players.remove("Zhang Jiankang");
        players.remove("Chen Zifan");
        players.remove("Bai Langning");
        players.remove("Mark King");
    }

    public static void main(String[] args) {
        JsonProcessor processor = new JsonProcessor();

        processor.initializePlayers("rankings_22_23.csv");

        // burn in with 2022-2023 season
        List<Match> matches2022_2023 = processor.readMatchesFromJson("season_2022-2023.json");
        processor.processMatches(matches2022_2023);
        // save the players at this point into csv file "players_after_2022-2023.csv"
        // with columns "name", "country", "currentFormPoints"
        try (Writer writer = new FileWriter("players_after_2022-2023.csv")) {
            writer.write("name,country,currentFormPoints\n");
            for (Player player : processor.getPlayers().values()) {
                writer.write(player.getName() + "," + player.getCountry() + "," + player.getCurrentFormPoints() + "\n");
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

        // store a hashmap of players and their points after 2022-2023 season for future use
        Map<String, Double> playersPointsAfter2022_2023 = new HashMap<>();
        for (Player player : processor.getPlayers().values()) {
            playersPointsAfter2022_2023.put(player.getName(), player.getCurrentFormPoints());
        }

        // 2023-2024 season
        List<Match> matches2023_2024 = processor.readMatchesFromJson("season_2023-2024.json");
        processor.processMatches(matches2023_2024);

        // store a hashmap of players and their points after 2023-2024 season for future use
        Map<String, Double> playersPointsAfter2023_2024 = new HashMap<>();
        for (Player player : processor.getPlayers().values()) {
            playersPointsAfter2023_2024.put(player.getName(), player.getCurrentFormPoints());
        }

        // 2024-2025 season
        List<Match> matches2024_2025 = processor.readMatchesFromJson("season_2024-2025.json");
        processor.processMatches(matches2024_2025);

        // store a hashmap of players and their points after 2024-2025 season for future use
        Map<String, Double> playersPointsAfter2024_2025 = new HashMap<>();
        for (Player player : processor.getPlayers().values()) {
            playersPointsAfter2024_2025.put(player.getName(), player.getCurrentFormPoints());
        }

        // 2025-2026 season
        List<Match> matches2025_2026 = processor.readMatchesFromJson("season_2025-2026.json");
        processor.processMatches(matches2025_2026);

        // store a hashmap of players and their points after 2025-2026 season for future use
        Map<String, Double> playersPointsAfter2025_2026 = new HashMap<>();
        for (Player player : processor.getPlayers().values()) {
            playersPointsAfter2025_2026.put(player.getName(), player.getCurrentFormPoints());
        }

        processor.deleteBannedPlayers();

        System.out.println("After processing 2025-2026 season:");
        System.out.println("There are " + processor.getPlayers().size() + " unique players in total.");
        System.out.println("Players after 2025-2026 season:");
        // print out players and their points, sorted by points from highest to lowest
        processor.getPlayers().values().stream()
                .sorted(Comparator.comparingDouble(Player::getCurrentFormPoints).reversed())
                .forEach(player -> System.out.println(player.getName() + " (" + player.getCountry() + "): " + player.getCurrentFormPoints()));

        // write a file "players_final.csv" with columns "name", "country", "currentFormPointsAfter2022_2023", "currentFormPointsAfter2023_2024", "currentFormPointsAfter2024_2025", "currentFormPointsAfter2025_2026"
        try (Writer writer = new FileWriter("players_final.csv")) {
            writer.write("name,country,currentFormPointsAfter2022_2023,currentFormPointsAfter2023_2024,currentFormPointsAfter2024_2025,currentFormPointsAfter2025_2026\n");
            for (Player player : processor.getPlayers().values()) {
                String name = player.getName();
                String country = player.getCountry();
                double pointsAfter2022_2023 = playersPointsAfter2022_2023.getOrDefault(name, 0.0);
                double pointsAfter2023_2024 = playersPointsAfter2023_2024.getOrDefault(name, 0.0);
                double pointsAfter2024_2025 = playersPointsAfter2024_2025.getOrDefault(name, 0.0);
                double pointsAfter2025_2026 = playersPointsAfter2025_2026.getOrDefault(name, 0.0);
                writer.write(name + "," + country + "," + pointsAfter2022_2023 + "," + pointsAfter2023_2024 + "," + pointsAfter2024_2025 + "," + pointsAfter2025_2026 + "\n");
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

        // write a file to keep players' score history
        // columns are "name", "country", "date", "score"
        try (Writer writer = new FileWriter("players_score_history.csv")) {
            writer.write("name,country,date,score\n");
            for (Player player : processor.getPlayers().values()) {
                String name = player.getName();
                String country = player.getCountry();
                for (ScoreDate scoreDate : player.getScoreHistory()) {
                    String date = scoreDate.getDate();
                    double score = scoreDate.getScore();
                    writer.write(name + "," + country + "," + date + "," + score + "\n");
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

    }
}
