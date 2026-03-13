import java.util.ArrayList;
import java.util.List;

public class Tournament{
    private String name;
    private Season season;
    private String cuetrackerURL;
    private String snookerorgURL;
    private List<Match> matches = new ArrayList<>();

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Season getSeason() {
        return season;
    }

    public void setSeason(Season season) {
        this.season = season;
    }

    public String getCuetrackerURL() {
        return cuetrackerURL;
    }

    public void setCuetrackerURL(String cuetrackerURL) {
        this.cuetrackerURL = cuetrackerURL;
    }

    public String getSnookerorgURL() {
        return snookerorgURL;
    }

    public void setSnookerorgURL(String snookerorgURL) {
        this.snookerorgURL = snookerorgURL;
    }

    public List<Match> getMatches() {
        return matches;
    }

    public void addMatch(Match match) {
        this.matches.add(match);
    }
}
