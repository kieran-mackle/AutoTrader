if (!window.autoscale_range) {
    window.autoscale_range = function (range, min, max, pad) {
        "use strict";
        if (min !== Infinity && max !== -Infinity) {
            pad         = pad ? (max - min) * .05 : 0;
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
    
    if (top_range) {
        let max = Math.max.apply(null, top_source.data['High'].slice(i, j)),
            min = Math.min.apply(null, top_source.data['Low'].slice(i, j));
        autoscale_range(top_range, min, max, true);
    }
    
    if (bot_range_1) {
        let max = Math.max.apply(null, bot_source_1.data['High'].slice(i, j)),
            min = Math.min.apply(null, bot_source_1.data['Low'].slice(i, j));
        autoscale_range(bot_range_1, min, max, true);
    }
    
    if (bot_range_2) {
        let max = Math.max.apply(null, bot_source_2.data['High'].slice(i, j)),
            min = Math.min.apply(null, bot_source_2.data['Low'].slice(i, j));
        autoscale_range(bot_range_2, min, max, true);
    }
    
    if (bot_range_3) {
        let max = Math.max.apply(null, bot_source_3.data['High'].slice(i, j)),
            min = Math.min.apply(null, bot_source_3.data['Low'].slice(i, j));
        autoscale_range(bot_range_3, min, max, true);
    }
    
    if (bot_range_4) {
        let max = Math.max.apply(null, bot_source_4.data['High'].slice(i, j)),
            min = Math.min.apply(null, bot_source_4.data['Low'].slice(i, j));
        autoscale_range(bot_range_4, min, max, true);
    }

}, 50);