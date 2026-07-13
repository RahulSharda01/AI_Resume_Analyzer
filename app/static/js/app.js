document.addEventListener('DOMContentLoaded', function () {
  const appForms = document.querySelectorAll('form');
  appForms.forEach(function (form) {
    form.addEventListener('submit', function () {
      const submitButton = form.querySelector('button[type=submit], input[type=submit]');
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.classList.add('disabled');
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
      }
    });
  });

  const alerts = document.querySelectorAll('.alert.alert-success.fade.show');
  alerts.forEach(function (alertElement) {
    setTimeout(function () {
      const alertInstance = bootstrap.Alert.getOrCreateInstance(alertElement);
      alertInstance.close();
    }, 3000);
  });
});
