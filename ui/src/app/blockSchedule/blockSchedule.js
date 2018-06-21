angular.module('schdl.blockSchedule', [])

.factory('ProcessSchedule', [function() {
  var colors=['#008000', '#CCCCFF', '#00CCFF', '#CCFFCC', '#FFFF99', '#99CCFF', '#FF99CC' ,'#CC99FF', '#FFCC99', '#3366FF', '#33CCCC', '#99CC00', '#FFCC00', '#FF9900', '#FF6600', '#666699', '#969696', '#339966', '#993300', '#008080', '#C0C0C0', '#808080', '#9999FF', '#CCFFFF', '#FF8080', '#0066CC', '#FF0000', '#00FF00', '#FFFF00', '#FF00FF', '#00FFFF'];
  // TODO(eitan): break this up into a bunch of smaller functions
  function processSchedule(schedule) {
    // schedule: as returned by /api/user (each item in the 'schedules' array) - the main part is the 'course_sections' array

    schedule = angular.copy(schedule);  // Make a copy - some modifications may be made
    var day, j, k, cs;
    var processed = {
      start: 1440,
      end: 0,
      days: ['su', 'm', 'tu', 'w', 'th', 'f', 'sa'],
      courses: 0,
      ruled_out: 0,
      su: [],
      m: [],
      tu: [],
      w: [],
      th: [],
      f: [],
      sa: []
    };

    // Create single-day events
    for (var i=0; i < schedule.course_sections.length; i++) {
      cs = schedule.course_sections[i];
      if (cs.user_status == 'no') {
        processed.ruled_out++;
        continue;
      }
      cs.color = colors[processed.courses % colors.length];
      processed.courses++;
      for (j=0; j < cs.times.length; j++) {
        var time = cs.times[j];
        if (time.start < processed.start) {
          processed.start = time.start;
        }
        if (time.end > processed.end) {
          processed.end = time.end;
        }
        for (k=0; k < time.days.length; k++) {
          day = time.days[k];
          processed[day].push({
            start: time.start,
            end: time.end,
            type: time.type,
            building: time.building,
            room: time.room,
            course_section: cs
          });
        }
      }
    }

    // Drop empty weekends
    if (processed.su.length === 0) {
      delete processed.su;
      processed.days.shift();
    }
    if (processed.sa.length === 0) {
      delete processed.sa;
      processed.days.pop();
    }

    // Round start and end to nearest 30 minutes
    processed.start = Math.floor(processed.start / 30) * 30;
    processed.end = Math.ceil(processed.end / 30) * 30;
    var times = [];
    for (i=processed.start; i < processed.end; i+=30) {
        times.push({time: i, half: i%60==30});
    }
    processed.times = times;
    // Break events into columns
    var cmp = function(a, b) {
      if (a.start == b.start) {
        return a.end - b.end;
      } else {
        return a.start - b.start;
      }
    };
    for (i=0; i < processed.days.length; i++) {
      day = processed.days[i];
      var items = processed[day];
      // Sort by starting time, ending time
      items.sort(cmp);
      // Break items into conflict groups
      var groups = [];
      for (j=0; j < items.length; j++) {
        cs = items[j];
        // Check if the item fits into the last created group
        var last_group = groups[groups.length - 1];
        if (last_group && cs.start < last_group.end && cs.end > last_group.start) {
          last_group.items.push(cs);
          if (cs.end > last_group.end) {
            last_group.end = cs.end;
          }
        } else {
          // Put it into a new group
          groups.push({
            start: cs.start,
            end: cs.end,
            items: [cs]
          });
        }
      }
      for (j=0; j < groups.length; j++) {
        var group = groups[j];
        // Create a set of non-conflicting columns for each group
        var columns = [];
        for (k=0; k < group.items.length; k++) {
          var cur_item = group.items[k], placed = false;
          // Check if an existing column can accomodate the current item
          for (var l=0; l < columns.length; l++) {
            var column = columns[l];
            if (column[column.length - 1].end <= cur_item.start) {
              column.push(cur_item);
              placed = true;
              break;
            }
          }
          // If not, make a new column
          if (!placed) {
            columns.push([cur_item]);
          }
        }
        // Tell each event about its position
        for (var colnum=0; colnum < columns.length; colnum++) {
          var col = columns[colnum];
          for (k=0; k < col.length; k++) {
            var cur_event = col[k];
            cur_event.column = colnum;
            cur_event.denominator = columns.length;
          }
        }
      }
    }
    return processed;
  }
  return processSchedule;
}])

.directive('schdlBlockSchedule', function() {
  return {
    restrict: 'E',
    scope: {
      schedule: '=',
      school: '='
    },
    controller: ['$scope', 'ProcessSchedule', 'Routes', '$window', function($scope, ProcessSchedule, Routes, $window) {
      $scope.Routes = Routes;
      $scope.$window = $window;
      // TODO(eitan): drop the 'new' and make the linter accept it
      $scope.$watch('schedule', function(newValue, oldValue) {
        $scope.processed = new ProcessSchedule(newValue);
      });
    }],
    templateUrl: '/static/blockSchedule/blockSchedule.tpl.html'
  };
})

;
