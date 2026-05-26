// Run with: osascript -l JavaScript ocr.js <imagePath>
ObjC.import('Foundation');
ObjC.import('Vision');

function run(argv) {
    if (argv.length < 1) {
        return "Usage: osascript -l JavaScript ocr.js <imagePath>";
    }
    var imagePath = argv[0];
    
    var url = $.NSURL.fileURLWithPath(imagePath);
    
    var requestHandler = $.VNImageRequestHandler.alloc.initWithURLOptions(url, $.NSDictionary.dictionary);
    if (requestHandler.isNil()) {
        return "Error: Could not create request handler for " + imagePath;
    }
    
    var request = $.VNRecognizeTextRequest.alloc.init;
    request.setRecognitionLevel(0); // 0 = VNRequestTextRecognitionLevelAccurate
    request.setUsesLanguageCorrection(true);
    
    var error = Ref();
    var requestsArray = $.NSArray.arrayWithObject(request);
    var success = requestHandler.performRequestsError(requestsArray, error);
    
    if (!success) {
        return "Error performing requests: " + error[0].description.js;
    }
    
    var results = request.results;
    var count = results.count;
    var recognizedText = [];
    for (var i = 0; i < count; i++) {
        var observation = results.objectAtIndex(i);
        var candidates = observation.topCandidates(1);
        if (candidates.count > 0) {
            var candidate = candidates.objectAtIndex(0);
            recognizedText.push(candidate.string.js);
        }
    }
    
    return recognizedText.join("\n");
}
