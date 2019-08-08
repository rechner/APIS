// ==== forms ====
function getAge(birthdate) {
    // FIXME: This date should be pulled from the start date for current event
    var curr  = new Date(2019, 7, 16); // Note: months are 0-indexed
    var diff = curr.getTime() - birthdate.getTime();
    return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
}
function toDateFormat(birthdate){
    var month = birthdate.getMonth();
    month = month + 1;
    return month + "/" + birthdate.getDate() + "/" + birthdate.getFullYear();
}
function parseDate(input) {
    // parse an ISO formatted date as localtime
    var parts = input.split('-');
    return new Date(parts[0], parts[1]-1, parts[2]);
}

function setTwoNumberDecimal(e) {
    this.value = parseFloat(this.value).toFixed(2);
}

function leftPad(value, length) {
    return ('0'.repeat(length) + value).slice(-length);
}

function getBirthdate() {
    var month = parseInt($("#birthMonth").val()) - 1;
    var day = $("#birthDay").val();
    var year = $("#birthYear").val();

    var birthdate = new Date(year, month, day);
    return birthdate;
}

