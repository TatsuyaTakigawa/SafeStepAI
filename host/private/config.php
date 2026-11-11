<?php
declare(strict_types=1);

return [
    'db_host' => getenv('DB_HOST') ?: 'db',
    'db_name' => getenv('DB_NAME') ?: 'safestep',
    'db_user' => getenv('DB_USER') ?: 'safestep',
    'db_pass' => getenv('DB_PASSWORD') ?: '',
    'username' => getenv('APP_USERNAME') ?: '',
    'password_hash' => getenv('APP_PASSWORD_HASH') ?: '',
    'api_key' => getenv('API_KEY') ?: '',
];
