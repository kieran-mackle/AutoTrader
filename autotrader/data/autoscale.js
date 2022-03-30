if (!window.autoscale_range) {
    window.autoscale_range = function (range, min, max, pad) {
        "use strict";
        if (min !== Infinity && max !== -Infinity) {
            pad         = pad ? (max - min) * .03 : 0;
            range.start = min - pad;
            range.end   = max + pad;
        } else console.error('AutoPlot data range error:', min, max, range);
    };
}

clearTimeout(window.autoscale_timeout);

window.autoscale_timeout = setTimeout(function () {
    "use strict";

    let i = Math.max(Math.floor(cb_obj.start), 0),
        j = Math.min(Math.ceil(cb_obj.end), source.data['High'].length);

    let max = Math.max.apply(null, source.data['High'].slice(i, j)),
        min = Math.min.apply(null, source.data['Low'].slice(i, j));
    autoscale_range(y_range, min, max, true);

}, 50);