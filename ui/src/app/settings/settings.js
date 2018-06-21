angular.module('schdl.settings', [])

.controller('SettingsCtrl', ['school', 'titleService', '$scope', '$localStorage', 'User', 'user', function(school, titleService, $scope, $localStorage, User, user) {
  $scope.settings = {
    primaryEmail: user.email[0],
    first: user.first,
    middle: user.middle,
    last: user.last,
    oldpwd: '',
    newpwd: '',
    repeatpwd: '',
    addEmail: '',
    deleteEmail: {}
  };
  $scope.updateName = function() {
    $scope.settings.nameResult = null;
    User.save({
      first: $scope.settings.first,
      middle: $scope.settings.middle,
      last: $scope.settings.last
    }, function(data) {
      if (data.status != 'noop') {
        $scope.get_user_data();
        $scope.settings.nameResult = 'success';
      }
    }, function() {
      $scope.settings.nameResult = 'error';
    });
  };
  $scope.updateEmail = function() {
    $scope.settings.emailResult = null;
    var addedEmail = false;
    var update = {
    };
    if ($scope.settings.primaryEmail != $localStorage.user.email[0]) {
      update.primary_email = $scope.settings.primaryEmail;
    }
    if ($scope.settings.addEmail) {
      update.add_email = $scope.settings.addEmail;
      addedEmail = true;
    }
    var deleteEmail = [];
    for (var i=1; i < $localStorage.user.email.length; i++) {
      var email = $localStorage.user.email[i];
      if ($scope.settings.deleteEmail[email]) {
        deleteEmail.push(email);
      }
    }
    if (deleteEmail.length) {
      update.delete_email = deleteEmail;
    }
    User.save(update, function(data) {
      if (data.status != 'noop') {
        $scope.get_user_data();
        $scope.settings.addEmail = '';
        $scope.settings.deleteEmail = {};
        $scope.settings.emailResult = addedEmail ? 'sent_verification':'success';
      }
    }, function(response) {
      if (response.data.status) {
        $scope.settings.emailResult = response.data.status;
      } else {
        $scope.settings.emailResult = 'error';
      }
    });
  };
  $scope.updatePassword = function() {
    if (!($scope.settings.oldpwd && $scope.settings.newpwd && $scope.settings.repeatpwd)) {
      return;
    }
    if ($scope.settings.newpwd != $scope.settings.repeatpwd) {
      $scope.settings.passwordResult = 'nomatch';
      return;
    }
    User.save({
      old_password: $scope.settings.oldpwd,
      new_password: $scope.settings.newpwd
    }, function(data) {
      if (data.status != 'noop') {
        $scope.settings.passwordResult = 'success';
      }
    }, function(response) {
      console.log(response);
      if (response.data.status) {
        $scope.settings.passwordResult = response.data.status;
      } else {
        $scope.settings.passwordResult = 'error';
      }
    });
    $scope.settings.passwordResult = null;
    $scope.settings.oldpwd = '';
    $scope.settings.newpwd = '';
    $scope.settings.repeatpwd = '';
  };
  titleService('Settings');
}])

;
