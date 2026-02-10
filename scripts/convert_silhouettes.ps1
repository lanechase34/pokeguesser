# create silhouette of image

cd frontend\public\silhouettes

Get-ChildItem *.png | ForEach-Object {
    Write-Host "Processing $($_.Name)..."
    magick $_.Name -channel RGB -evaluate set 0 +channel "temp_$($_.Name)"
    Move-Item -Force "temp_$($_.Name)" $_.Name
}

Write-Host "Done!"