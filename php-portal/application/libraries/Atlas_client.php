<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Atlas_client Library
 * Integrates CodeIgniter 3 with the Python Project Atlas FastAPI backend.
 * Provides timeout protection, cURL error recovery, and robust payload validation.
 */
class Atlas_client {

    protected $CI;
    protected $api_base_url;
    protected $api_key;
    protected $timeout_seconds;

    public function __construct() {
        $this->CI =& get_instance();
        
        // Load configuration or environment variables
        $this->api_base_url = getenv('ATLAS_API_URL') ? getenv('ATLAS_API_URL') : 'http://127.0.0.1:8000';
        $this->api_key = getenv('ATLAS_API_KEY') ? getenv('ATLAS_API_KEY') : 'atlas_secret_key_12345';
        $this->timeout_seconds = 30;
    }

    /**
     * Sends a query to the Python FastAPI /chat endpoint
     *
     * @param string $client_id E.g., 'C-01' or 'C-02'
     * @param string $message The user's research question
     * @return array Decoded response structure with error handling
     */
    public function send_chat($client_id, $message) {
        $url = rtrim($this->api_base_url, '/') . '/chat';
        $payload = json_encode([
            'client_id' => $client_id,
            'message'   => $message
        ]);

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout_seconds);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->api_key
        ]);

        $raw_response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curl_error = curl_error($ch);
        curl_close($ch);

        if ($curl_error) {
            return [
                'success' => false,
                'answer'  => 'Connection Timeout: The AI Copilot service did not respond within ' . $this->timeout_seconds . ' seconds. Our engineering team has been alerted.',
                'citations' => [],
                'confidence' => 0.0,
                'conflicts' => [],
                'derived_values' => [],
                'escalated' => true
            ];
        }

        if ($http_code !== 200) {
            return [
                'success' => false,
                'answer'  => 'Service Error (HTTP ' . $http_code . '): The AI Copilot is temporarily unavailable. Please try again or consult your assigned market research analyst.',
                'citations' => [],
                'confidence' => 0.0,
                'conflicts' => [],
                'derived_values' => [],
                'escalated' => true
            ];
        }

        $decoded = json_decode($raw_response, true);
        if (!$decoded || !isset($decoded['answer'])) {
            return [
                'success' => false,
                'answer'  => 'Invalid Response Format: Unable to parse AI Copilot synthesis.',
                'citations' => [],
                'confidence' => 0.0,
                'conflicts' => [],
                'derived_values' => [],
                'escalated' => true
            ];
        }

        $decoded['success'] = true;
        return $decoded;
    }

    /**
     * Submits thumbs-up / thumbs-down rating to /feedback
     */
    public function send_feedback($client_id, $question, $answer, $rating) {
        $url = rtrim($this->api_base_url, '/') . '/feedback';
        $payload = json_encode([
            'client_id' => $client_id,
            'question'  => $question,
            'answer'    => $answer,
            'rating'    => $rating
        ]);

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->api_key
        ]);

        $res = curl_exec($ch);
        curl_close($ch);
        return json_decode($res, true);
    }
}
