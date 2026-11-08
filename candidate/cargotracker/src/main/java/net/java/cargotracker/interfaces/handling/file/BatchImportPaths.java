package net.java.cargotracker.interfaces.handling.file;

import java.io.File;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

final class BatchImportPaths {
    static final String JOB_NAME = "EventFilesProcessorJob";
    static final Path ROOT = Path.of("/opt/jboss/wildfly/standalone/data/cargo-import");
    static final Path INCOMING = ROOT.resolve("incoming");
    static final Path ARCHIVE = ROOT.resolve("archive");
    static final Path FAILED = ROOT.resolve("failed");
    static final String ENABLED_PROPERTY = "lab.import.enabled";

    static Path requireDirectory(Path expected, String configuredValue) throws IOException {
        if (configuredValue == null || !expected.toString().equals(configuredValue)
                || !expected.normalize().equals(expected)
                || !expected.startsWith(ROOT)) {
            throw new IOException("Configured import directory is not an approved private directory");
        }
        Path current = expected.getRoot();
        for (Path component : expected) {
            current = current.resolve(component);
            if (Files.isSymbolicLink(current)
                    || !Files.isDirectory(current, LinkOption.NOFOLLOW_LINKS)) {
                throw new IOException("Import directory chain contains an unsafe component");
            }
        }
        return expected;
    }

    static List<File> incomingFiles(String configuredValue) throws IOException {
        Path directory = requireDirectory(INCOMING, configuredValue);
        List<File> files = new ArrayList<>();
        try (DirectoryStream<Path> entries = Files.newDirectoryStream(directory)) {
            for (Path entry : entries) {
                BasicFileAttributes attributes = Files.readAttributes(entry,
                        BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                if (attributes.isSymbolicLink() || !attributes.isRegularFile()
                        || !entry.toAbsolutePath().normalize().getParent().equals(INCOMING)) {
                    throw new IOException("Import staging contains a non-regular or unsafe entry");
                }
                files.add(entry.toFile());
            }
        }
        files.sort(Comparator.comparing(File::getName));
        return List.copyOf(files);
    }

    static File requireIncomingFile(File file) throws IOException {
        Path path = file.toPath().toAbsolutePath().normalize();
        if (!INCOMING.equals(path.getParent()) || Files.isSymbolicLink(path)
                || !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("Checkpoint references an unsafe import file");
        }
        return path.toFile();
    }

    static java.io.BufferedWriter openAppendOutput(Path directory, String configuredDirectory,
            String filename) throws IOException {
        Path approved = requireDirectory(directory, configuredDirectory);
        if (filename == null || !filename.matches("[A-Za-z0-9_-]+\\.csv")) {
            throw new IOException("Invalid generated import output name");
        }
        Path output = approved.resolve(filename);
        if (!output.getParent().equals(approved)) {
            throw new IOException("Import output escaped its approved directory");
        }
        if (Files.exists(output, LinkOption.NOFOLLOW_LINKS)
                && !Files.isRegularFile(output, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("Existing import output is not a regular file");
        }
        return new java.io.BufferedWriter(java.nio.channels.Channels.newWriter(
                Files.newByteChannel(output, java.util.Set.of(
                        java.nio.file.StandardOpenOption.CREATE,
                        java.nio.file.StandardOpenOption.WRITE,
                        java.nio.file.StandardOpenOption.APPEND,
                        LinkOption.NOFOLLOW_LINKS)),
                java.nio.charset.StandardCharsets.UTF_8));
    }

    private BatchImportPaths() {}
}
