import pandas as pd
import numpy as np
from django.shortcuts import render
from django.http import JsonResponse
import os
import json

def aggregation_view(request):
    """
    Handles file upload, performs custom aggregation, and returns a JSON response.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            # Handle cases where the document might be missing
            return render(request, 'core/aggregation_page.html', {'error': 'Please upload a CSV file.'})

        file_path = os.path.join('media', uploaded_file.name)
        
        try:
            if not os.path.exists('media'):
                os.makedirs('media')
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            df = pd.read_csv(file_path)

            group_by_col = None
            aggregate_col = None

            group_keywords = ['name', 'category', 'type', 'id', 'platform', 'publisher']
            for col in df.columns:
                if any(keyword in col.lower() for keyword in group_keywords) and not pd.api.types.is_numeric_dtype(df[col]):
                    group_by_col = col
                    break
            
            if not group_by_col:
                for col in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        group_by_col = col
                        break

            agg_keywords = ['sales', 'count', 'score', 'amount', 'rating']
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    if any(keyword in col.lower() for keyword in agg_keywords):
                        aggregate_col = col
                        break
            
            if not aggregate_col:
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        aggregate_col = col
                        break

            if not group_by_col or not aggregate_col:
                error = "Could not automatically detect suitable columns for grouping and aggregation."
                # We render the page with an error instead of returning JSON
                return render(request, 'core/aggregation_page.html', {'error': error})

            def product_agg(series):
                return np.prod(series)

            df[aggregate_col] = pd.to_numeric(df[aggregate_col], errors='coerce').fillna(1)
            aggregated_data = df.groupby(group_by_col)[aggregate_col].agg(product_agg)
            
            result_df = aggregated_data.reset_index()
            result_df.columns = [group_by_col, f'{aggregate_col}_product']
            result_html = result_df.to_html(classes=['table', 'table-striped'])
            
            return render(request, 'core/aggregation_page.html', {
                'results': result_html,
                'group_by_col': group_by_col,
                'aggregate_col': aggregate_col
            })

        except (ValueError, FileNotFoundError) as e:
            return render(request, 'core/aggregation_page.html', {'error': str(e)})
        except Exception as e:
            return render(request, 'core/aggregation_page.html', {'error': f"An unexpected error occurred: {e}"})
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    return render(request, 'core/aggregation_page.html')