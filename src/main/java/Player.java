import java.util.ArrayList;
import java.util.List;

public class Player{
    private String name;
    private String country;
    private double currentFormPoints;
    private List<ScoreDate> scoreHistory = new ArrayList<>();
    private String lastMatchDate;

    public String getLastMatchDate() {
        return lastMatchDate;
    }

    public void setLastMatchDate(String lastMatchDate) {
        this.lastMatchDate = lastMatchDate;
    }

    public List<ScoreDate> getScoreHistory() {
        return scoreHistory;
    }

    public void addScoreDate(ScoreDate scoreDate) {
        this.scoreHistory.add(scoreDate);
    }

    public void addScoreDate(String date, double score) {
        this.scoreHistory.add(new ScoreDate(date, score));
    }

    public Player(String name, String country){
        this.name = name;
        this.country = country;
        this.currentFormPoints = 1500;
    }

    public Player(String name, String country, double initialPoints){
        this.name = name;
        this.country = country;
        this.currentFormPoints = initialPoints;
    }

    // override equals and hashCode so that two players with the same name are considered equal
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Player player = (Player) o;
        return name.equals(player.name);
    }

    @Override
    public int hashCode() {
        return name.hashCode();
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public double getCurrentFormPoints() {
        return currentFormPoints;
    }

    public void setCurrentFormPoints(double currentFormPoints) {
        this.currentFormPoints = currentFormPoints;
    }
}
