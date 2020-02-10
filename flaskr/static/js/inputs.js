

function addOne(type) {
    switch (type) {
        case 'component' :
            // TODO: validate if component was already added
            if ($(`#quantitytemplate`).val() > 0) {
                display(inputs=['typetemplate', 'nametemplate', 'quantitytemplate', 'unittemplate'],
                output='component');
            }
            break;
        case 'group':
            if ($(`#grouplabeltemplate`).val() ||
            $(`#groupwelltemplate`).val() || $(`#groupsampletemplate`).val()) {
                display(inputs=['grouplabeltemplate', 'groupwelltemplate', 'groupsampletemplate'],
                output='group');
            }
            break;
        case 'swap':
            if ($(`#swapfromtemplate`).val() || $(`#swaptotemplate`).val()) {
                display(inputs=['swapfromtemplate', 'swaptotemplate', 'bidirectionaltemplate'],
                output='swap');
            }
            break;
    }
}

var componentcount = 1;
var groupcount = 1;
var swapcount = 1;

function display(inputs, output) {
    outputspan = document.getElementById(output);
    outputfield = document.createElement("div");
    outputfield.id = output + getCounter(output);

    for (var i=0; i<inputs.length; i++) {
        entry = document.getElementById(inputs[i]);
        if (entry.checked) {
            outputfield.innerText += '  bidirectional';
        }
        outputfield.innerText += '  ' + entry.value;
    }
    outputfield.innerHTML += '<br>';
    outputspan.appendChild(outputfield);

    switch (output) {
        case 'component': componentcount += 1; break;
        case 'group': groupcount += 1; break;
        case 'swap': swapcount += 1; break;
    }
}

function deleteOne(output) {
    document.getElementById(output + (getCounter(output)-1)).remove();
    switch (output) {
        case 'component': componentcount -= 1; break;
        case 'group': groupcount -= 1; break;
        case 'swap': swapcount -= 1; break;
    }
}

function getCounter(table) {
    switch (table) {
        case 'component': return componentcount;
        case 'group': return groupcount;
        case 'swap': return swapcount;
    }
}