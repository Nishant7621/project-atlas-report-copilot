<?php
/**
 * CodeIgniter 3 Entry Point for Project Atlas
 */
define('ENVIRONMENT', isset($_SERVER['CI_ENV']) ? $_SERVER['CI_ENV'] : 'development');

$system_path = 'system';
$application_folder = 'application';
$view_folder = '';

if (defined('STDIN')) {
    chdir(dirname(__FILE__));
}

if (($_temp = realpath($system_path)) !== FALSE) {
    $system_path = $_temp.DIRECTORY_SEPARATOR;
} else {
    $system_path = strtr(rtrim($system_path, '/\\'), '/\\', DIRECTORY_SEPARATOR.DIRECTORY_SEPARATOR).DIRECTORY_SEPARATOR;
}

define('SELF', pathinfo(__FILE__, PATHINFO_BASENAME));
define('BASEPATH', $system_path);
define('FCPATH', dirname(__FILE__).DIRECTORY_SEPARATOR);
define('SYSDIR', basename(BASEPATH));
define('APPPATH', $application_folder.DIRECTORY_SEPARATOR);

if (!file_exists(BASEPATH . 'core/CodeIgniter.php')) {
    // Standalone fallback router if full system folder is not mounted
    require_once APPPATH . 'libraries/Atlas_client.php';
    
    // Simple direct routing for standalone PHP development
    $uri = $_SERVER['REQUEST_URI'] ?? '/';
    if (strpos($uri, 'chat/send') !== false) {
        $client_id = $_POST['client_id'] ?? 'C-01';
        $message   = $_POST['message'] ?? '';
        $atlas = new Atlas_client();
        $res = $atlas->send_chat($client_id, $message);
        $res['answer_escaped'] = nl2br(htmlspecialchars($res['answer'], ENT_QUOTES, 'UTF-8'));
        header('Content-Type: application/json');
        echo json_encode($res);
        exit;
    }
    
    // Default render view
    $current_client = $_GET['client_id'] ?? 'C-01';
    function site_url($path) { return '/' . ltrim($path, '/'); }
    class DummySecurity {
        public function get_csrf_token_name() { return 'csrf_test_name'; }
        public function get_csrf_hash() { return md5('atlas_csrf_salt'); }
    }
    $security = new DummySecurity();
    require APPPATH . 'views/chat_view.php';
    exit;
}

require_once BASEPATH.'core/CodeIgniter.php';
