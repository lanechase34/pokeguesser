# convert images to webp format

cd frontend\public\images

Get-ChildItem *.png | ForEach-Object {
    $webpName = $_.BaseName + ".webp"
    Write-Host "Converting $($_.Name) to $webpName..."
    magick $_.Name -quality 80 $webpName
    if ($LASTEXITCODE -eq 0) {
        Remove-Item $_.Name
        Write-Host "Deleted $($_.Name)"
    }
}

Write-Host "Done!"