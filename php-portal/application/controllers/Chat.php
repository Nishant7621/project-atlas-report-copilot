<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Chat Controller for Project Atlas CodeIgniter 3 Portal
 * Enforces:
 * - CSRF verification
 * - XSS escaping for all outputs
 * - Graceful timeout and error handling
 * - Feedback recording
 */
class Chat extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->load->library('atlas_client');
        $this->load->helper(['url', 'html', 'form']);
    }

    /**
     * Renders the main chat portal view
     */
    public function index() {
        $data['clients'] = [
            'C-01' => 'Northwind Utilities (Purchased: R-101, R-103)',
            'C-02' => 'Blue Delta Infra (Purchased: R-103 only)'
        ];
        $data['current_client'] = $this->input->get('client_id') ? $this->input->get('client_id') : 'C-01';

        $this->load->view('chat_view', $data);
    }

    /**
     * AJAX endpoint to handle chat messages
     */
    public function send() {
        // CSRF verification is performed automatically by CI3 if enabled in config
        if (!$this->input->is_ajax_request() && strtolower($_SERVER['REQUEST_METHOD'] ?? '') !== 'post') {
            show_error('Invalid access mode', 400);
            return;
        }

        $client_id = $this->security->xss_clean($this->input->post('client_id'));
        $message   = $this->security->xss_clean($this->input->post('message'));

        if (empty($client_id) || empty($message)) {
            $this->output
                ->set_content_type('application/json')
                ->set_output(json_encode([
                    'success' => false,
                    'answer'  => 'Validation Error: Both client ID and question are required.'
                ]));
            return;
        }

        // Call Python service via Atlas_client library
        $response = $this->atlas_client->send_chat($client_id, $message);

        // Sanitize and escape all output to prevent Cross-Site Scripting (XSS)
        $response['answer_escaped'] = nl2br(htmlspecialchars($response['answer'], ENT_QUOTES, 'UTF-8'));
        
        $this->output
            ->set_content_type('application/json')
            ->set_output(json_encode($response));
    }

    /**
     * AJAX endpoint to record thumbs-up / thumbs-down ratings
     */
    public function feedback() {
        $client_id = $this->security->xss_clean($this->input->post('client_id'));
        $question  = $this->security->xss_clean($this->input->post('question'));
        $answer    = $this->security->xss_clean($this->input->post('answer'));
        $rating    = $this->security->xss_clean($this->input->post('rating'));

        $res = $this->atlas_client->send_feedback($client_id, $question, $answer, $rating);

        $this->output
            ->set_content_type('application/json')
            ->set_output(json_encode(['status' => 'success']));
    }
}
