/*
  IsoLens YARA Ruleset: Packers and Evasion Techniques
*/

rule UPX_Packer {
    meta:
        description = "Detects UPX executable compressor sections or signatures"
        severity = "medium"
        category = "packer"
        author = "IsoLens"
    strings:
        $upx0 = "UPX0" ascii
        $upx1 = "UPX1" ascii
        $upx2 = "UPX2" ascii
        $upx_sig = "!UPX" ascii
    condition:
        2 of ($upx0, $upx1, $upx2, $upx_sig)
}

rule Anti_Debugging_APIs {
    meta:
        description = "Detects common anti-debugging and analysis evasion API strings"
        severity = "medium"
        category = "evasion"
        author = "IsoLens"
    strings:
        $api1 = "IsDebuggerPresent" ascii wide nocase
        $api2 = "CheckRemoteDebuggerPresent" ascii wide nocase
        $api3 = "NtQueryInformationProcess" ascii wide nocase
        $api4 = "OutputDebugString" ascii wide nocase
        $api5 = "FindWindowA" ascii wide nocase
        $api6 = "GetTickCount" ascii wide nocase
    condition:
        2 of them
}

rule Virtual_Machine_Evasion {
    meta:
        description = "Detects artifacts and strings used to detect VirtualBox, VMware, or QEMU"
        severity = "high"
        category = "evasion"
        author = "IsoLens"
    strings:
        $vbox1 = "VBoxGuestAdditions" ascii wide nocase
        $vbox2 = "VBOX" ascii wide
        $vbox3 = "HARDWARE\\ACPI\\DSDT\\VBOX__" ascii wide nocase
        $vmware1 = "VMware" ascii wide nocase
        $vmware2 = "vmtoolsd" ascii wide nocase
        $qemu1 = "QEMU" ascii wide nocase
        $qemu2 = "qemu-ga" ascii wide nocase
        $wine = "wine_get_unix_file_name" ascii
    condition:
        any of them
}
