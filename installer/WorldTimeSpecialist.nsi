!define APP_NAME "World Time Specialist"
!define APP_EXE "WorldTimeSpecialist.exe"
!define APP_VERSION "1.0.0"
!define COMPANY "World Time Specialist"

OutFile "..\release\WorldTimeSpecialist-Setup.exe"
InstallDir "$PROGRAMFILES\WorldTimeSpecialist"
InstallDirRegKey HKCU "Software\WorldTimeSpecialist" "InstallDir"
RequestExecutionLevel user

Name "${APP_NAME}"
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${COMPANY}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"

Icon "..\assets\clock.ico"
UninstallIcon "..\assets\clock.ico"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "..\dist\WorldTimeSpecialist\*"

  WriteRegStr HKCU "Software\WorldTimeSpecialist" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateShortCut "$DESKTOP\World Time Specialist.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}"
  CreateDirectory "$SMPROGRAMS\World Time Specialist"
  CreateShortCut "$SMPROGRAMS\World Time Specialist\World Time Specialist.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\World Time Specialist.lnk"
  Delete "$SMPROGRAMS\World Time Specialist\World Time Specialist.lnk"
  RMDir "$SMPROGRAMS\World Time Specialist"

  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\WorldTimeSpecialist"
SectionEnd
