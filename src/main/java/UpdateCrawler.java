import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.By;
import org.openqa.selenium.PageLoadStrategy;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.io.*;
import java.time.LocalDate;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import java.util.Random;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

public class UpdateCrawler {
    private WebDriver driver;
    private WebDriverWait wait;
    private LocalDate date =  LocalDate.now();
    private static final String SEASON_DIVIDER = "06-01";

    public UpdateCrawler() {
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--window-size=1920,1080");
        options.setPageLoadStrategy(PageLoadStrategy.EAGER);
        driver = new ChromeDriver(options);
        driver.manage().timeouts().pageLoadTimeout(30, TimeUnit.SECONDS);
        wait = new WebDriverWait(driver, 10);
    }

    public void endUpdateCrawl() {
        if (driver != null) {
            driver.quit();
        }
    }

    public String decideCurrentSeason(){
        String currentYear = date.getYear() + "";
        // compare date and currentYear+SEASON_DIVIDER
        if (date.isBefore(LocalDate.parse(currentYear + "-" + SEASON_DIVIDER))) {
            return (date.getYear() - 1) + "-" + currentYear;
        }
        else {
            return currentYear + "-" + (date.getYear() + 1);
        }
    }

    public boolean checkSeasonFile(String seasonName){
        // check if the file "season" + season + ".json" exists
        String fileName = "season_" + seasonName + ".json";
        Path file = Paths.get(fileName);
        return Files.exists(file);
    }

    public Season getNewSeason(String seasonName){
        Season season = new Season();
        String seasonUrl = "https://cuetracker.net/seasons/"  + seasonName;
        season.setCuetrackerURL(seasonUrl);
        season.setSeason(seasonName);
        System.out.println("Processing Season: " + season.getSeason());

        try {
            driver.get(seasonUrl);
            wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("table")));
            List<WebElement> tournamentAnchors = driver.findElements(
                    By.xpath("//a[contains(@href, '/tournaments/')]"));
            Set<String> seenTournamentUrls = new HashSet<>();
            for  (WebElement anchor : tournamentAnchors) {
                String tournamentURL = anchor.getAttribute("href");
                String tournamentName = anchor.getText().trim();
                if (isQualifiedTournament(tournamentName)
                        && tournamentURL != null
                        && seenTournamentUrls.add(tournamentURL)) {
                    Tournament tournament = new Tournament();
                    tournament.setName(tournamentName);
                    tournament.setCuetrackerURL(tournamentURL);
                    season.addTournament(tournament);
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return season;
    }

    static boolean isQualifiedTournament(String tournamentName) {
        if (tournamentName == null || tournamentName.trim().isEmpty()) {
            return false;
        }
        String normalizedName = tournamentName.toLowerCase(Locale.ROOT);
        return !normalizedName.contains("q school") && !normalizedName.contains("6-reds");
    }

    public void processTournament(Season season){
        List<Tournament> tournaments = season.getTournaments();
        int testCounter = 0;
        Random random = new Random();
        for  (Tournament tournament : tournaments) {
//            if (testCounter++ > 0) {
//                break;
//            }
            // print out processing tournament
            System.out.println("Processing Tournament: " + tournament.getName());
            try {
                // Wait for a minimum of 1+ seconds
                int minWait = 1000;
                int randomWait = random.nextInt(2000);
                int totalWait = minWait + randomWait;

                System.out.println("Waiting for " + (totalWait / 1000.0) + " seconds...");
                Thread.sleep(totalWait);

            } catch (InterruptedException e) {
                // This catches the error if the sleep is interrupted
                Thread.currentThread().interrupt();
                System.out.println("Sleep interrupted!");
            }
            try{
                String tournamentURL = tournament.getCuetrackerURL();
                driver.get(tournamentURL);
                List<WebElement> matchContainers =
                        driver.findElements(
                                By.xpath("//div[starts-with(@id, 'round') and contains(@id, 'match')]"));
                for (WebElement container : matchContainers) {
                    Match match = new Match();

                    WebElement p1Element = container.findElement(By.xpath(".//div[1]/div[2]/div[1]"));
                    WebElement p2Element = container.findElement(By.xpath(".//div[1]/div[2]/div[3]"));
                    String player1 = p1Element.getText().trim();
                    if (player1.contains("Walkover")){
                        continue;
                    }
                    String player2 = p2Element.getText().trim();
                    match.setPlayer1(player1);
                    match.setPlayer2(player2);

                    WebElement score1Element = container.findElement(By.xpath(".//div[1]/div[2]/div[2]/span[1]"));
                    WebElement bestOfFrames = container.findElement(By.xpath(".//div[1]/div[2]/div[2]/span[2]"));
                    WebElement score2Element = container.findElement(By.xpath(".//div[1]/div[2]/div[2]/span[3]"));
                    int socre1 = Integer.parseInt(score1Element.getText().trim());
                    int socre2 = Integer.parseInt(score2Element.getText().trim());
                    String bestOfText = bestOfFrames.getText().trim();
                    bestOfText = bestOfText.substring(1, bestOfText.length() - 1);
                    int bestOf = Integer.parseInt(bestOfText);
                    match.setPlayer1Score(socre1);
                    match.setPlayer2Score(socre2);
                    match.setBestOfFrames(bestOf);

                    WebElement dateElement = container.findElement(
                            By.xpath(".//div[1]/div[4]/div[2]/div[1]/div[1]"));
                    match.setDate(dateElement.getText().trim());

                    WebElement player1BreaksElement = container.findElement(
                            By.xpath(".//div[contains(text(), '50+ Breaks')]/following-sibling::div//div[contains(@class, 'col-4')][1]"));
                    WebElement player2BreaksElement = container.findElement(
                            By.xpath(".//div[contains(text(), '50+ Breaks')]/following-sibling::div//div[contains(@class, 'col-4')][2]"));
                    // breaks are string like "50, 70, 90". make them into list of integers
                    String player1BreaksText = player1BreaksElement.getText().trim();
                    String player2BreaksText = player2BreaksElement.getText().trim();
                    List<Integer> player1Breaks = Arrays.stream(player1BreaksText.split(","))
                            .map(String::trim)
                            .filter(s -> !s.isEmpty())
                            .map(Integer::parseInt)
                            .collect(Collectors.toList());
                    List<Integer> player2Breaks = Arrays.stream(player2BreaksText.split(","))
                            .map(String::trim)
                            .filter(s -> !s.isEmpty())
                            .map(Integer::parseInt)
                            .collect(Collectors.toList());
                    match.setBreaksPlayer1(player1Breaks);
                    match.setBreaksPlayer2(player2Breaks);

                    String player1Country = "Unknown";
                    String player2Country = "Unknown";
                    try{
                        WebElement player1CountryElement = container.findElement(
                                By.xpath(".//div[1]/div[2]/div[1]//img"));
                        player1Country = player1CountryElement.getAttribute("alt").trim();
                    }
                    catch (Exception e){
                        System.out.println("Country not found!");
                    }
                    try {
                        WebElement player2CountryElement = container.findElement(
                                By.xpath(".//div[1]/div[2]/div[3]//img"));
                        player2Country = player2CountryElement.getAttribute("alt").trim();
                    }
                    catch (Exception e){
                        System.out.println("Country not found!");
                    }

                    match.setPlayer1Country(player1Country);
                    match.setPlayer2Country(player2Country);

                    WebElement roundElement = container.findElement(
                            By.xpath(".//div[1]//h5"));
                    match.setRound(roundElement.getText().trim());


                    tournament.addMatch(match);
                }
            }
            catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public void processSingleTournament(Tournament tournament) {
        System.out.println("Processing Tournament: " + tournament.getName());
        Random random = new Random();
        try {
            // Wait for a minimum of 1+ seconds
            int minWait = 1000;
            int randomWait = random.nextInt(2000);
            int totalWait = minWait + randomWait;

            System.out.println("Waiting for " + (totalWait / 1000.0) + " seconds...");
            Thread.sleep(totalWait);

        } catch (InterruptedException e) {
            // This catches the error if the sleep is interrupted
            Thread.currentThread().interrupt();
            System.out.println("Sleep interrupted!");
        }
        try{
            String tournamentURL = tournament.getCuetrackerURL();
            driver.get(tournamentURL);
            List<WebElement> matchContainers =
                    driver.findElements(
                            By.xpath("//div[starts-with(@id, 'round') and contains(@id, 'match')]"));
            for (WebElement container : matchContainers) {
                Match match = new Match();

                WebElement p1Element = container.findElement(By.xpath(".//div[1]/div[2]/div[1]"));
                WebElement p2Element = container.findElement(By.xpath(".//div[1]/div[2]/div[3]"));
                String player1 = p1Element.getText().trim();
                if (player1.contains("Walkover")){
                    continue;
                }
                String player2 = p2Element.getText().trim();
                match.setPlayer1(player1);
                match.setPlayer2(player2);

                WebElement score1Element = container.findElement(By.xpath(".//div[1]/div[2]/div[2]/span[1]"));
                WebElement bestOfFrames = container.findElement(By.xpath(".//div[1]/div[2]/div[2]/span[2]"));
                WebElement score2Element = container.findElement(By.xpath(".//div[1]/div[2]/div[2]/span[3]"));
                int socre1 = Integer.parseInt(score1Element.getText().trim());
                int socre2 = Integer.parseInt(score2Element.getText().trim());
                String bestOfText = bestOfFrames.getText().trim();
                bestOfText = bestOfText.substring(1, bestOfText.length() - 1);
                int bestOf = Integer.parseInt(bestOfText);
                match.setPlayer1Score(socre1);
                match.setPlayer2Score(socre2);
                match.setBestOfFrames(bestOf);

                WebElement dateElement = container.findElement(
                        By.xpath(".//div[1]/div[4]/div[2]/div[1]/div[1]"));
                match.setDate(dateElement.getText().trim());

                WebElement player1BreaksElement = container.findElement(
                        By.xpath(".//div[contains(text(), '50+ Breaks')]/following-sibling::div//div[contains(@class, 'col-4')][1]"));
                WebElement player2BreaksElement = container.findElement(
                        By.xpath(".//div[contains(text(), '50+ Breaks')]/following-sibling::div//div[contains(@class, 'col-4')][2]"));
                // breaks are string like "50, 70, 90". make them into list of integers
                String player1BreaksText = player1BreaksElement.getText().trim();
                String player2BreaksText = player2BreaksElement.getText().trim();
                List<Integer> player1Breaks = Arrays.stream(player1BreaksText.split(","))
                        .map(String::trim)
                        .filter(s -> !s.isEmpty())
                        .map(Integer::parseInt)
                        .collect(Collectors.toList());
                List<Integer> player2Breaks = Arrays.stream(player2BreaksText.split(","))
                        .map(String::trim)
                        .filter(s -> !s.isEmpty())
                        .map(Integer::parseInt)
                        .collect(Collectors.toList());
                match.setBreaksPlayer1(player1Breaks);
                match.setBreaksPlayer2(player2Breaks);

                String player1Country = "Unknown";
                String player2Country = "Unknown";
                try{
                    WebElement player1CountryElement = container.findElement(
                            By.xpath(".//div[1]/div[2]/div[1]//img"));
                    player1Country = player1CountryElement.getAttribute("alt").trim();
                }
                catch (Exception e){
                    System.out.println("Country not found!");
                }
                try {
                    WebElement player2CountryElement = container.findElement(
                            By.xpath(".//div[1]/div[2]/div[3]//img"));
                    player2Country = player2CountryElement.getAttribute("alt").trim();
                }
                catch (Exception e){
                    System.out.println("Country not found!");
                }

                match.setPlayer1Country(player1Country);
                match.setPlayer2Country(player2Country);

                WebElement roundElement = container.findElement(
                        By.xpath(".//div[1]//h5"));
                match.setRound(roundElement.getText().trim());


                tournament.addMatch(match);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void updateSeason(String seasonName){
        System.out.println("Updating season: " + seasonName);
        String jsonFile = "season_" + seasonName + ".json";
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        Season existingSeason = null;
        try (Reader reader = new FileReader(jsonFile)) {
            existingSeason = gson.fromJson(reader, Season.class);
        }
        catch (Exception e) {
            e.printStackTrace();
            System.out.println("Error reading existing season file. Aborting update.");
            return;
        }

        Season refreshedSeason = getNewSeason(seasonName);
        if (refreshedSeason.getTournaments().isEmpty()) {
            System.err.println("No qualifying tournaments found; keeping the existing season file unchanged.");
            return;
        }

        Map<String, Tournament> existingTournaments = new HashMap<>();
        if (existingSeason.getTournaments() != null) {
            for (Tournament tournament : existingSeason.getTournaments()) {
                existingTournaments.put(tournamentKey(tournament), tournament);
            }
        }

        for (Tournament tournament : refreshedSeason.getTournaments()) {
            processSingleTournament(tournament);

            Tournament previous = existingTournaments.get(tournamentKey(tournament));
            if (tournament.getMatches().isEmpty()
                    && previous != null
                    && previous.getMatches() != null
                    && !previous.getMatches().isEmpty()) {
                System.out.println("Keeping previously scraped matches for " + tournament.getName()
                        + " because the refresh returned no matches.");
                for (Match match : previous.getMatches()) {
                    tournament.addMatch(match);
                }
            }
        }

        try (Writer writer = new FileWriter(jsonFile)) {
            gson.toJson(refreshedSeason, writer);
            System.out.println("Successfully refreshed " + refreshedSeason.getTournaments().size()
                    + " tournaments in " + jsonFile);
        } catch (Exception writeException) {
            System.err.println("Failed to write updated data to JSON file.");
            writeException.printStackTrace();
        }
    }

    private static String tournamentKey(Tournament tournament) {
        String url = tournament.getCuetrackerURL();
        if (url != null && !url.trim().isEmpty()) {
            return "url:" + url.trim().toLowerCase(Locale.ROOT);
        }
        String name = tournament.getName() == null ? "" : tournament.getName().trim();
        return "name:" + name.toLowerCase(Locale.ROOT);
    }

    public static void main(String[] args) {
        UpdateCrawler updateCrawler = null;
        try {
            updateCrawler = new UpdateCrawler();
            String currentSeason = updateCrawler.decideCurrentSeason();
            if (!updateCrawler.checkSeasonFile(currentSeason)){
                Season newSeason = updateCrawler.getNewSeason(currentSeason);
                updateCrawler.processTournament(newSeason);
                Gson gson = new GsonBuilder().setPrettyPrinting().create();
                String fileName = "season_" + currentSeason + ".json";
                try (Writer writer = new FileWriter(fileName)) {
                    gson.toJson(newSeason, writer);
                }
                catch (IOException e) {
                    e.printStackTrace();
                }
            }
            else {
                updateCrawler.updateSeason(currentSeason);
            }
        } finally {
            if (updateCrawler != null) {
                updateCrawler.endUpdateCrawl();
            }
        }
    }
}
