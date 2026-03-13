import java.util.ArrayList;
import java.util.List;

public class Season{
    private String season;
    private List<Tournament> tournaments = new ArrayList<>();
    private String cuetrackerURL;
    private String snookerorgURL;

    public String getSeason() {
        return season;
    }

    public void setSeason(String season) {
        this.season = season;
    }

    public List<Tournament> getTournaments() {
        return tournaments;
    }

    public void setTournaments(List<Tournament> tournaments) {
        this.tournaments = tournaments;
    }

    public void addTournament(Tournament tournament) {
        this.tournaments.add(tournament);
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
}
