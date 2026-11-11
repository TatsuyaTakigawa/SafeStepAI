CREATE TABLE IF NOT EXISTS events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    device_name VARCHAR(64) NOT NULL,
    occurred_at DATETIME NOT NULL,
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    track_id BIGINT UNSIGNED NOT NULL,
    direction ENUM('UP', 'DOWN') NOT NULL,
    is_reverse TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    INDEX idx_events_occurred_at (occurred_at),
    INDEX idx_events_device_occurred (device_name, occurred_at),
    INDEX idx_events_reverse (is_reverse)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
