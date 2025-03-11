/**
 * JavaScript for the Shift admin form
 * Shows/hides fields based on the selected shift type
 */
(function ($) {
  $(document).ready(function () {
    // Function to toggle fields based on shift type
    function toggleShiftTypeFields() {
      var shiftType = $('#id_shift_type').val();

      if (shiftType === 'recurring') {
        $('.field-day_of_week').show();
        $('.field-specific_date').hide();
        $('.shift-recurring').show();
        $('.shift-one-time').hide();
      } else {
        $('.field-day_of_week').hide();
        $('.field-specific_date').show();
        $('.shift-recurring').hide();
        $('.shift-one-time').show();
      }
    }

    // Initial toggle
    toggleShiftTypeFields();

    // Toggle on change
    $('#id_shift_type').change(toggleShiftTypeFields);
  });
})(django.jQuery);
