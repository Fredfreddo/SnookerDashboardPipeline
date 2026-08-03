import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collections;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public final class SeasonFileUtils {
    private static final Pattern SEASON_FILE_PATTERN =
            Pattern.compile("season_(\\d{4}-\\d{4})\\.json");

    private SeasonFileUtils() {
    }

    public static List<Path> findSeasonFiles(Path directory) {
        try (Stream<Path> paths = Files.list(directory)) {
            return paths
                    .filter(Files::isRegularFile)
                    .filter(path -> SEASON_FILE_PATTERN.matcher(path.getFileName().toString()).matches())
                    .sorted((left, right) -> seasonName(left).compareTo(seasonName(right)))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            e.printStackTrace();
            return Collections.emptyList();
        }
    }

    public static String seasonName(Path seasonFile) {
        Matcher matcher = SEASON_FILE_PATTERN.matcher(seasonFile.getFileName().toString());
        if (!matcher.matches()) {
            throw new IllegalArgumentException("Not a season JSON file: " + seasonFile);
        }
        return matcher.group(1);
    }

    public static String csvColumnName(String seasonName) {
        return "currentFormPointsAfter" + seasonName.replace('-', '_');
    }
}
