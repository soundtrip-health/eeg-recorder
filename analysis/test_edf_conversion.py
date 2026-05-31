"""
Unit tests for EDF conversion functionality

Run with: pytest test_edf_conversion.py -v
"""

import pytest
import pyedflib
import os
from pathlib import Path
from utils import json_to_edf, load_eeg, export_to_edf


# Fixtures
@pytest.fixture
def test_json_file():
    """Path to test JSON file"""
    return 'data/MuseS-5743_2025-10-17T19_30_11.142Z.json'


@pytest.fixture
def output_dir(tmp_path):
    """Temporary directory for output files"""
    return tmp_path


@pytest.fixture
def sample_annotations():
    """Sample annotations for testing"""
    return {
        "eyes_open": [
            {"start": 0, "duration": 30},
            {"start": 60, "duration": 30}
        ],
        "eyes_closed": [
            {"start": 30, "duration": 30},
            {"start": 90, "duration": 30}
        ]
    }


@pytest.fixture
def complex_annotations():
    """More complex annotations with multiple events"""
    return {
        "baseline": [{"start": 0, "duration": 60}],
        "task_1": [{"start": 60, "duration": 120}],
        "rest": [{"start": 180, "duration": 30}],
        "task_2": [{"start": 210, "duration": 120}]
    }


# Basic Conversion Tests
class TestBasicConversion:
    """Test basic EDF conversion without annotations"""
    
    def test_json_to_edf_all_data(self, test_json_file, output_dir):
        """Test converting JSON to EDF with all data types"""
        output_file = output_dir / "test_all.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_All',
            include_motion=True,
            include_ppg=True,
            line_freq=60
        )
        
        assert os.path.exists(result)
        
        # Verify file contents
        edf = pyedflib.EdfReader(result)
        assert edf.signals_in_file == 13  # 4 EEG + 6 motion + 3 PPG
        assert edf.getPatientName() == 'Test All'
        edf.close()
    
    def test_json_to_edf_eeg_only(self, test_json_file, output_dir):
        """Test converting JSON to EDF with only EEG data"""
        output_file = output_dir / "test_eeg.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_EEG',
            include_motion=False,
            include_ppg=False,
            line_freq=60
        )
        
        assert os.path.exists(result)
        
        # Verify file contents
        edf = pyedflib.EdfReader(result)
        assert edf.signals_in_file == 4  # 4 EEG channels only
        labels = edf.getSignalLabels()
        assert 'TP9' in labels
        assert 'AF7' in labels
        assert 'AF8' in labels
        assert 'TP10' in labels
        edf.close()
    
    def test_json_to_edf_no_filtering(self, test_json_file, output_dir):
        """Test conversion without notch filtering"""
        output_file = output_dir / "test_no_filter.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_NoFilter',
            include_motion=False,
            include_ppg=False,
            line_freq=None  # Disable filtering
        )
        
        assert os.path.exists(result)
        
        edf = pyedflib.EdfReader(result)
        assert edf.signals_in_file == 4
        edf.close()
    
    def test_export_to_edf_separate_load(self, test_json_file, output_dir):
        """Test export_to_edf with separately loaded data"""
        output_file = output_dir / "test_export.edf"
        
        # Load data first
        metadata, eeg_df, motion_df, ppg_df = load_eeg(test_json_file, line_freq=60)
        
        # Export
        result = export_to_edf(
            str(output_file),
            metadata,
            eeg_df,
            motion_df,
            ppg_df,
            subject_name='Test_Export',
            include_motion=True,
            include_ppg=True
        )
        
        assert os.path.exists(result)
        
        edf = pyedflib.EdfReader(result)
        assert edf.signals_in_file == 13
        edf.close()


# Annotation Tests
class TestAnnotations:
    """Test annotation functionality"""
    
    def test_json_to_edf_with_annotations(self, test_json_file, output_dir, sample_annotations):
        """Test converting with annotations"""
        output_file = output_dir / "test_annotations.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Annotations',
            include_motion=False,
            include_ppg=False,
            annotations=sample_annotations
        )
        
        assert os.path.exists(result)
        
        # Verify annotations
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        
        assert len(times) == 4  # 2 eyes_open + 2 eyes_closed
        assert 'eyes_open' in texts
        assert 'eyes_closed' in texts
        
        edf.close()
    
    def test_export_to_edf_with_annotations(self, test_json_file, output_dir, complex_annotations):
        """Test export_to_edf with annotations"""
        output_file = output_dir / "test_export_annot.edf"
        
        metadata, eeg_df, motion_df, ppg_df = load_eeg(test_json_file, line_freq=60)
        
        result = export_to_edf(
            str(output_file),
            metadata,
            eeg_df,
            motion_df,
            ppg_df,
            subject_name='Test_Export_Annot',
            include_motion=False,
            include_ppg=False,
            annotations=complex_annotations
        )
        
        assert os.path.exists(result)
        
        # Verify annotations
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        
        assert len(times) == 4  # baseline, task_1, rest, task_2
        assert 'baseline' in texts
        assert 'task_1' in texts
        assert 'rest' in texts
        assert 'task_2' in texts
        
        edf.close()
    
    def test_no_annotations(self, test_json_file, output_dir):
        """Test that conversion works without annotations"""
        output_file = output_dir / "test_no_annot.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_No_Annot',
            include_motion=False,
            include_ppg=False,
            annotations=None
        )
        
        assert os.path.exists(result)
        
        # Verify no annotations
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        assert len(times) == 0
        edf.close()
    
    def test_annotation_timing(self, test_json_file, output_dir):
        """Test that annotation timing is preserved correctly"""
        output_file = output_dir / "test_timing.edf"
        
        annotations = {
            "event_1": [{"start": 10.5, "duration": 5.5}],
            "event_2": [{"start": 20.0, "duration": 10.0}]
        }
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Timing',
            include_motion=False,
            include_ppg=False,
            annotations=annotations
        )
        
        # Verify timing
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        
        assert len(times) == 2
        assert abs(times[0] - 10.5) < 0.1  # Allow small floating point error
        assert abs(durations[0] - 5.5) < 0.1
        assert abs(times[1] - 20.0) < 0.1
        assert abs(durations[1] - 10.0) < 0.1
        
        edf.close()
    
    def test_multiple_events_same_label(self, test_json_file, output_dir):
        """Test multiple events with the same label"""
        output_file = output_dir / "test_multiple.edf"
        
        annotations = {
            "stimulus": [
                {"start": 10, "duration": 2},
                {"start": 20, "duration": 2},
                {"start": 30, "duration": 2},
                {"start": 40, "duration": 2}
            ]
        }
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Multiple',
            include_motion=False,
            include_ppg=False,
            annotations=annotations
        )
        
        # Verify all events present
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        
        assert len(times) == 4
        assert all(text == 'stimulus' for text in texts)
        
        edf.close()
    
    def test_overlapping_annotations(self, test_json_file, output_dir):
        """Test that overlapping annotations work correctly"""
        output_file = output_dir / "test_overlap.edf"
        
        annotations = {
            "task_block": [{"start": 0, "duration": 120}],
            "attention_check": [
                {"start": 30, "duration": 5},
                {"start": 90, "duration": 5}
            ]
        }
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Overlap',
            include_motion=False,
            include_ppg=False,
            annotations=annotations
        )
        
        # Verify overlapping annotations
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        
        assert len(times) == 3
        assert 'task_block' in texts
        assert 'attention_check' in texts
        
        edf.close()


# Signal Quality Tests
class TestSignalQuality:
    """Test signal data quality and integrity"""
    
    def test_signal_sample_rates(self, test_json_file, output_dir):
        """Test that signal sample rates are correct"""
        output_file = output_dir / "test_rates.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Rates',
            include_motion=True,
            include_ppg=True,
            line_freq=60
        )
        
        edf = pyedflib.EdfReader(result)
        
        # Check EEG channels (should be 256 Hz)
        for i in range(4):
            assert edf.getSampleFrequency(i) == 256
        
        # Check motion channels (should be 52 Hz)
        for i in range(4, 10):
            assert edf.getSampleFrequency(i) == 52
        
        # Check PPG channels (should be 64 Hz)
        for i in range(10, 13):
            assert edf.getSampleFrequency(i) == 64
        
        edf.close()
    
    def test_signal_labels(self, test_json_file, output_dir):
        """Test that signal labels are correct"""
        output_file = output_dir / "test_labels.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Labels',
            include_motion=True,
            include_ppg=True,
            line_freq=60
        )
        
        edf = pyedflib.EdfReader(result)
        labels = edf.getSignalLabels()
        
        # Check EEG labels
        assert 'TP9' in labels
        assert 'AF7' in labels
        assert 'AF8' in labels
        assert 'TP10' in labels
        
        # Check motion labels
        assert 'acc_x' in labels
        assert 'acc_y' in labels
        assert 'acc_z' in labels
        assert 'gyr_x' in labels
        assert 'gyr_y' in labels
        assert 'gyr_z' in labels
        
        # Check PPG labels
        assert 'ppg0' in labels
        assert 'ppg1' in labels
        assert 'ppg2' in labels
        
        edf.close()
    
    def test_physical_dimensions(self, test_json_file, output_dir):
        """Test that physical dimensions (units) are correct"""
        output_file = output_dir / "test_dims.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Dims',
            include_motion=True,
            include_ppg=True,
            line_freq=60
        )
        
        edf = pyedflib.EdfReader(result)
        
        # Check EEG units (microvolts)
        for i in range(4):
            assert edf.getPhysicalDimension(i) == 'uV'
        
        # Check accelerometer units (g)
        for i in range(4, 7):
            assert edf.getPhysicalDimension(i) == 'g'
        
        # Check gyroscope units (deg/s)
        for i in range(7, 10):
            assert edf.getPhysicalDimension(i) == 'deg/s'
        
        # Check PPG units (arbitrary units)
        for i in range(10, 13):
            assert edf.getPhysicalDimension(i) == 'au'
        
        edf.close()
    
    def test_data_not_empty(self, test_json_file, output_dir):
        """Test that exported signals contain data"""
        output_file = output_dir / "test_data.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Data',
            include_motion=False,
            include_ppg=False,
            line_freq=60
        )
        
        edf = pyedflib.EdfReader(result)
        
        # Read first channel and check it has data
        signal = edf.readSignal(0)
        assert len(signal) > 0
        assert signal.std() > 0  # Should have variation
        
        edf.close()


# Edge Cases and Error Handling
class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_annotations(self, test_json_file, output_dir):
        """Test with empty annotation dictionary"""
        output_file = output_dir / "test_empty_annot.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Empty',
            include_motion=False,
            include_ppg=False,
            annotations={}  # Empty dict
        )
        
        assert os.path.exists(result)
        
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        assert len(times) == 0
        edf.close()
    
    def test_zero_duration_annotation(self, test_json_file, output_dir):
        """Test annotation with zero duration (instantaneous event)"""
        output_file = output_dir / "test_zero_duration.edf"
        
        annotations = {
            "button_press": [
                {"start": 10, "duration": 0},
                {"start": 20, "duration": 0}
            ]
        }
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Test_Zero',
            include_motion=False,
            include_ppg=False,
            annotations=annotations
        )
        
        assert os.path.exists(result)
        
        edf = pyedflib.EdfReader(result)
        times, durations, texts = edf.readAnnotations()
        assert len(times) == 2
        assert all(d == 0 for d in durations)
        edf.close()
    
    def test_subject_name_with_spaces(self, test_json_file, output_dir):
        """Test that subject names with spaces are handled correctly"""
        output_file = output_dir / "test_spaces.edf"
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Subject 01',
            include_motion=False,
            include_ppg=False
        )
        
        assert os.path.exists(result)
        
        edf = pyedflib.EdfReader(result)
        # Spaces should be preserved or replaced with underscores
        patient_name = edf.getPatientName()
        assert patient_name in ['Subject 01', 'Subject_01']
        edf.close()
    
    def test_automatic_output_filename(self, test_json_file, output_dir):
        """Test automatic generation of output filename"""
        # This test is tricky because it would save in the same directory as input
        # We'll test the logic by checking that output filename is generated
        # when not provided
        pass  # Skip for now as it would create files in data directory


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_workflow(self, test_json_file, output_dir):
        """Test complete workflow from JSON to EDF with all features"""
        output_file = output_dir / "test_complete.edf"
        
        annotations = {
            "baseline": [{"start": 0, "duration": 60}],
            "task": [{"start": 60, "duration": 120}],
            "recovery": [{"start": 180, "duration": 60}]
        }
        
        result = json_to_edf(
            test_json_file,
            str(output_file),
            subject_name='Integration_Test',
            include_motion=True,
            include_ppg=True,
            line_freq=60,
            annotations=annotations
        )
        
        assert os.path.exists(result)
        
        # Comprehensive verification
        edf = pyedflib.EdfReader(result)
        
        # Check signals
        assert edf.signals_in_file == 13
        
        # Check metadata
        assert 'Integration Test' in edf.getPatientName()
        assert edf.getFileDuration() > 0
        
        # Check annotations
        times, durations, texts = edf.readAnnotations()
        assert len(times) == 3
        assert set(texts) == {'baseline', 'task', 'recovery'}
        
        # Check signal quality
        signal = edf.readSignal(0)
        assert len(signal) > 0
        
        edf.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

