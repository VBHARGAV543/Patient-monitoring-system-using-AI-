# Add 9 dummy GENERAL ward patients
$patients = @(
    @{name="John Smith"; age=45; gender="Male"; problem="Hypertension monitoring"},
    @{name="Maria Garcia"; age=32; gender="Female"; problem="Post-surgery recovery"},
    @{name="David Lee"; age=58; gender="Male"; problem="Diabetes management"},
    @{name="Sarah Johnson"; age=27; gender="Female"; problem="Asthma observation"},
    @{name="Michael Brown"; age=41; gender="Male"; problem="Cardiac checkup"},
    @{name="Emily Davis"; age=35; gender="Female"; problem="Pneumonia treatment"},
    @{name="James Wilson"; age=52; gender="Male"; problem="Back pain assessment"},
    @{name="Lisa Anderson"; age=29; gender="Female"; problem="Migraine monitoring"},
    @{name="Robert Taylor"; age=63; gender="Male"; problem="Arthritis care"}
)

$url = "http://localhost:8000/api/patient/admit"
$i = 1

foreach ($patient in $patients) {
    $body = @{
        name = $patient.name
        age = $patient.age
        gender = $patient.gender
        problem = $patient.problem
        patient_type = "GENERAL"
        demo_mode = $true
        hardware_mode = $false
        weight = 60.0 + (Get-Random -Minimum 0 -Maximum 40)
        height = 155.0 + (Get-Random -Minimum 0 -Maximum 30)
        medical_history = "Previous checkups normal"
        allergies = "None"
        current_medications = "None"
        emergency_contact = "+91 987654321$i"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
        Write-Host "✓ Created patient $i/9: $($patient.name) (ID: $($response.id))" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to create $($patient.name): $($_.Exception.Message)" -ForegroundColor Red
    }
    $i++
}

Write-Host "`nDone! 9 dummy patients added." -ForegroundColor Cyan
