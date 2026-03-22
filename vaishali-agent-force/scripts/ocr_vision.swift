#!/usr/bin/env swift
// ocr_vision.swift — Extract text from an image using macOS Vision framework.
//
// Usage:  swift ocr_vision.swift /path/to/image.jpg
// Output: Recognised text lines to stdout, one per observation.
//
// This replaces the fragile AppleScript approach with a direct Swift script
// that runs reliably on any Mac with Xcode Command Line Tools installed.

import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count > 1 else {
    fputs("Usage: swift ocr_vision.swift <image_path>\n", stderr)
    exit(1)
}

let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let tiffData = image.tiffRepresentation,
      let cgImage = NSBitmapImageRep(data: tiffData)?.cgImage else {
    fputs("Error: Could not load image at \(imagePath)\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

do {
    try handler.perform([request])
} catch {
    fputs("Vision error: \(error.localizedDescription)\n", stderr)
    exit(1)
}

guard let observations = request.results else {
    exit(0)
}

for observation in observations {
    if let candidate = observation.topCandidates(1).first {
        print(candidate.string)
    }
}
