import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.nio.file.Path;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;

public class UpcomingMatchScraper {

    public static void main(String[] args) {
        // 1. Load the Standard Player List
        Set<String> standardNames = loadPlayerList("player_list.txt");
        if (standardNames.isEmpty()) {
            System.out.println("Warning: player_list.txt is empty or missing. Will use raw scraped names.");
        }

        // 2. Setup WebDriver
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--window-size=1920,1080");
        options.addArguments("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");

        WebDriver driver = new ChromeDriver(options);
        WebDriverWait wait = new WebDriverWait(driver, 10);

        LocalDate today = LocalDate.now();
        LocalDate tomorrow = today.plusDays(1);
        int year = today.getYear();
        int month = today.getMonthValue();
        String season = (month >= 6) ? year + "-" + (year + 1) : (year - 1) + "-" + year;

        String url = "https://www.snooker.org/res/index.asp?template=24&season=" + season.substring(0, 4);
        String csvFilePath = "upcoming_matches.csv";

        try (PrintWriter writer = new PrintWriter(new FileWriter(csvFilePath))) {
            writer.println("Player 1,Player 2,Best Of,Date");

            driver.get(url);

            // 3. Find the main table
            List<WebElement> tables = driver.findElements(By.xpath("//table[@class='display matches']"));
            if (tables.isEmpty()) {
                System.out.println("Table 'display matches' not found. Returning empty CSV.");
                return; // Exits safely, leaving an empty CSV with just headers
            }

            // 4. Find the first thead with class "tourMain" and its following tbody
            WebElement thead = null;
            WebElement tbody = null;
            try {
                thead = driver.findElement(By.xpath("//table[@class='display matches']//thead[contains(@class, 'tourMain')][1]"));
                String tourName = thead.getText();
                System.out.println("Found matches of : " + tourName);

                // write tourName in a txt
                Files.writeString(Path.of("tourName.txt"), tourName);

                tbody = thead.findElement(By.xpath("following-sibling::tbody[1]"));
            } catch (Exception e) {
                System.out.println("Could not find the target thead/tbody structure. Returning empty CSV.");
                return;
            }

            // 5. Iterate through rows
            List<WebElement> rows = tbody.findElements(By.tagName("tr"));
            String currentBestOf = "9"; // Default fallback
            String currentDate = "Unknown Date";
            int matchCount = 0;

            for (WebElement row : rows) {
                String rowText = row.getText();

                // Track "Best of X" which snooker.org often puts in sub-headers or round headers
                WebElement bestOfSpan = row.findElement(By.xpath("//span[contains(@title, 'Best of')]"));
                if (bestOfSpan != null) {
                    //String bestOfText = bestOfSpan.getText();
                    currentBestOf = bestOfSpan.getText();
                }

                // If the row has player links, it's a match row
                List<WebElement> playerLinks = row.findElements(By.xpath(".//a[contains(@href, 'player')]"));
                if (playerLinks.size() >= 2) {

                    // On snooker.org, the date is usually in the first TD of the row
                    WebElement dateElement = row.findElement(By.xpath(".//span[@class='scheduled']"));
                    //String dateString = dateElement.getText();
                    currentDate = dateElement.getText();
                    // change date into "yyyy-mm-dd" format
                    String fullDateStr = currentDate + " " + year;
                    // 2. Define the input format
                    // Use Locale.ENGLISH to ensure "Mon" and "Mar" are parsed correctly
                    DateTimeFormatter inputFormatter = DateTimeFormatter.ofPattern("EEE dd MMM HH:mm yyyy");
                    // 3. Parse to LocalDateTime
                    LocalDateTime dateTime = LocalDateTime.parse(fullDateStr, inputFormatter);
                    // 4. Format to the target string "yyyy-MM-dd"
                    // Note: Use 'MM' for month. 'mm' represents minutes in Java.
                    currentDate = dateTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));


                    String rawPlayer1 = playerLinks.get(0).getText().trim();
                    String rawPlayer2 = playerLinks.get(1).getText().trim();
                    System.out.println("Match between " + rawPlayer1 + " and " + rawPlayer2);

                    // Apply the standardization logic
                    String player1 = matchPlayerName(rawPlayer1, standardNames);
                    String player2 = matchPlayerName(rawPlayer2, standardNames);

                    writer.printf("\"%s\",\"%s\",%s,\"%s\"%n", player1, player2, currentBestOf, currentDate);
                    matchCount++;
                }
            }

            System.out.println("Successfully scraped " + matchCount + " upcoming matches from snooker.org.");

        } catch (Exception e) {
            System.err.println("An error occurred during scraping:");
            e.printStackTrace();
        } finally {
            driver.quit();
        }
    }

    // --- HELPER METHODS ---

    /**
     * Reads the player_list.txt file into a List of strings.
     */
    private static Set<String> loadPlayerList(String filepath) {
        // take each row in the file as a name and add to a set for O(1) lookups
        Set<String> players = new HashSet<>();
        try {
            List<String> lines = Files.readAllLines(Paths.get(filepath));
            for (String line : lines) {
                players.add(line.trim());
            }
        }
        catch (Exception e) {
            System.err.println("Could not load player list.");
        }
        return players;
    }

    /**
     * Standardizes a scraped name against the known player list using multi-pass logic.
     */
    private static String matchPlayerName(String scrapedName, Set<String> standardNames) {
        // 1. Exact match (case-sensitive)
        if (standardNames.contains(scrapedName)) {
            return scrapedName;
        }

        // 2, swap fist and second names, check if contains
        String[] names = scrapedName.split(" ");
        StringBuilder swapped = new StringBuilder();
        // swapped = second element in names + first element in names + the rest
        if  (names.length > 1) {
            swapped.append(names[1]).append(" ").append(names[0]);
            for (int i = 2; i < names.length; i++) {
                swapped.append(" ").append(names[i]);
            }
        }
        String swappedName = swapped.toString();
        if (standardNames.contains(swappedName)) {
            return swappedName;
        }
        // 3, remove middle name
        StringBuilder shortened = new StringBuilder();
        if (names.length > 2) {
            shortened.append(names[2]).append(" ").append(names[0]);
        }
        String shortenedName = shortened.toString();
        if (standardNames.contains(shortenedName)) {
            return shortenedName;
        }
        // 4, check only first two names
        StringBuilder longerName = new StringBuilder();
        if (names.length > 2) {
            longerName.append(names[0]).append(" ").append(names[1]);
        }
        String longerNameString = longerName.toString();
        if (standardNames.contains(longerNameString)) {
            return longerNameString;
        }

        return scrapedName;
    }
    
    private static String makeDisplayingName(String playerName) {
        // make all word's first character uppercases and the rest lowercases
        String[] parts = playerName.split(" ");
        StringBuilder displayName = new StringBuilder();
        for (String part : parts) {
            if (!part.isEmpty()) {
                displayName.append(Character.toUpperCase(part.charAt(0)));
                if (part.length() > 1) {
                    displayName.append(part.substring(1).toLowerCase());
                }
            }
            displayName.append(" ");
        }
        return displayName.toString();
    }
}