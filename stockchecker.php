<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class FlipkartProductController extends Controller
{
    /**
     * Endpoint: accepts pincode + product_url, expands short URL,
     * calls Python terminal-script.py, and returns its result.
     */
    public function check(Request $request)
    {
        // 1. Validate input from frontend
        $validated = $request->validate([
            'pincode'     => ['required', 'string'],
            'product_url' => ['required', 'url'],
        ]);

        $pincode    = $validated['pincode'];
        $productUrl = $validated['product_url'];

        // 2. Expand shortened link to full Flipkart product URL
        $expandedUrl = $this->expandUrl($productUrl);

        // 3. Run Python terminal-script.py with expanded URL + pincode
        //    Adjust these paths to match your server
        $pythonPath = '/usr/bin/python3';              // path to python
        $scriptPath = base_path('terminal-script.py'); // path to terminal-script.py

        $process = new Process([$pythonPath, $scriptPath, $expandedUrl, $pincode]);
        $process->setTimeout(60); // seconds

        $process->run();

        if (! $process->isSuccessful()) {
            throw new ProcessFailedException($process);
        }

        $output = trim($process->getOutput());

        // 4. Try to decode Python output as JSON
        $decoded = json_decode($output, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            // Python did not return valid JSON – return raw output
            return response()->json([
                'success' => false,
                'error'   => 'Invalid JSON from Python script',
                'raw'     => $output,
            ], 500);
        }

        // 5. Return decoded JSON back to frontend
        return response()->json([
            'success' => true,
            'data'    => $decoded,
        ]);
    }

    /**
     * Follow redirects to expand a shortened URL (fkrt.it -> full Flipkart URL).
     */
    protected function expandUrl(string $url): string
    {
        $ch = curl_init($url);

        curl_setopt_array($ch, [
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_NOBODY         => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_MAXREDIRS      => 10,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
        ]);

        curl_exec($ch);
        $finalUrl = curl_getinfo($ch, CURLINFO_EFFECTIVE_URL);
        curl_close($ch);

        return $finalUrl ?: $url;
    }
}