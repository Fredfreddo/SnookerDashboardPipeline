import java.util.ArrayList;
import java.util.List;

public class Match{
    private String player1;
    private String player2;
    private int player1Score;
    private int player2Score;
    private int bestOfFrames;
    private String player1Country;
    private String player2Country;

    public int getOriginalIndex() {
        return originalIndex;
    }

    public void setOriginalIndex(int originalIndex) {
        this.originalIndex = originalIndex;
    }

    private int originalIndex;

    public String getRound() {
        return round;
    }

    public void setRound(String round) {
        this.round = round;
    }

    private String round;

    public String getPlayer1Country() {
        return player1Country;
    }

    public void setPlayer1Country(String player1Country) {
        this.player1Country = player1Country;
    }

    public String getPlayer2Country() {
        return player2Country;
    }

    public void setPlayer2Country(String player2Country) {
        this.player2Country = player2Country;
    }

    public String getPlayer1() {
        return player1;
    }

    public void setPlayer1(String player1) {
        this.player1 = player1;
    }

    public String getPlayer2() {
        return player2;
    }

    public void setPlayer2(String player2) {
        this.player2 = player2;
    }

    public int getPlayer1Score() {
        return player1Score;
    }

    public void setPlayer1Score(int player1Score) {
        this.player1Score = player1Score;
    }

    public int getPlayer2Score() {
        return player2Score;
    }

    public void setPlayer2Score(int player2Score) {
        this.player2Score = player2Score;
    }

    public int getBestOfFrames() {
        return bestOfFrames;
    }

    public void setBestOfFrames(int bestOfFrames) {
        this.bestOfFrames = bestOfFrames;
    }

    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public List<Integer> getBreaksPlayer1() {
        return breaksPlayer1;
    }

    public void setBreaksPlayer1(List<Integer> breaksPlayer1) {
        this.breaksPlayer1 = breaksPlayer1;
    }

    public List<Integer> getBreaksPlayer2() {
        return breaksPlayer2;
    }

    public void setBreaksPlayer2(List<Integer> breaksPlayer2) {
        this.breaksPlayer2 = breaksPlayer2;
    }

    private String date;
    private List<Integer> breaksPlayer1 = new ArrayList<>();
    private List<Integer> breaksPlayer2 = new ArrayList<>();
}
