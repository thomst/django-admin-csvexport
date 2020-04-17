$(document).ready(function () {
    inputs = $('input[id$="_select_all"]');
    console.log(inputs);
    inputs.change(function() {
        options = $('#' + this.id.slice(0,-11)).find('input');
        if (this.checked) {
            options.each(function(){$(this).prop('checked', true);})
        } else {
            options.each(function(){$(this).prop('checked', false);})
        }
    });
})
