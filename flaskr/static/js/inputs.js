

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
                display(inputs=['grouplabeltemplate', 'groupwelltemplate', 'groupsampletemplate',
                        'groupcontroltemplate'],
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
    inputfield = document.createElement("input");
    inputfield.name = output + getCounter(output);
    inputfield.style.visibility = 'hidden';

    outputvalue = document.createElement("a");
    outputvalue.id = output + getCounter(output);

    for (var i=0; i<inputs.length; i++) {
        entry = document.getElementById(inputs[i]);
        if (entry.checked) {
            outputvalue.innerText += ' bidirectional';
            inputfield.innerText += '  bidirectional';
        }
        let value = entry.value;
        if (i > 0) {
            value = ' ' + entry.value;
        }

        outputvalue.innerText += value;
        inputfield.value += value;
    }

    outputvalue.innerHTML += '<br>';
    displayedoutput = document.getElementById(output);
    displayedoutput.appendChild(outputvalue);
    displayedoutput.appendChild(inputfield);

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